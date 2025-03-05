# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.

import copy
import json
import logging
import os
import re
import secrets
import string
import uuid
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import httpx
from pydantic import TypeAdapter

from llama_stack.apis.agents import (
    AgentConfig,
    AgentToolGroup,
    AgentToolGroupWithArgs,
    AgentTurnCreateRequest,
    AgentTurnResponseEvent,
    AgentTurnResponseEventType,
    AgentTurnResponseStepCompletePayload,
    AgentTurnResponseStepProgressPayload,
    AgentTurnResponseStepStartPayload,
    AgentTurnResponseStreamChunk,
    AgentTurnResponseTurnAwaitingInputPayload,
    AgentTurnResponseTurnCompletePayload,
    AgentTurnResponseTurnStartPayload,
    AgentTurnResumeRequest,
    Attachment,
    Document,
    InferenceStep,
    ShieldCallStep,
    StepType,
    ToolExecutionStep,
    Turn,
)
from llama_stack.apis.common.content_types import (
    URL,
    TextContentItem,
    ToolCallDelta,
    ToolCallParseStatus,
)
from llama_stack.apis.inference import (
    ChatCompletionResponseEventType,
    CompletionMessage,
    Inference,
    Message,
    SamplingParams,
    SystemMessage,
    ToolDefinition,
    ToolResponse,
    ToolResponseMessage,
    UserMessage,
)
from llama_models.datatypes import StopReason
from llama_stack.apis.safety import Safety
from llama_stack.apis.tools import RAGDocument, RAGQueryConfig, ToolGroups, ToolInvocationResult, ToolRuntime
from llama_stack.apis.vector_io import VectorIO
from llama_stack.models.llama.datatypes import (
    ToolParamDefinition,
)
from llama_models.datatypes import BuiltinTool, ToolCall
from llama_stack.providers.utils.kvstore import KVStore
from llama_stack.providers.utils.memory.vector_store import concat_interleaved_content
from llama_stack.providers.utils.telemetry import tracing

from .persistence import AgentPersistence
from .safety import SafetyException, ShieldRunnerMixin

log = logging.getLogger(__name__)


def make_random_string(length: int = 8):
    return "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(length))


TOOLS_ATTACHMENT_KEY_REGEX = re.compile(r"__tools_attachment__=(\{.*?\})")
MEMORY_QUERY_TOOL = "query_from_memory"
WEB_SEARCH_TOOL = "web_search"
RAG_TOOL_GROUP = "builtin::rag"


class ChatAgent(ShieldRunnerMixin):
    def __init__(
        self,
        agent_id: str,
        agent_config: AgentConfig,
        tempdir: str,
        inference_api: Inference,
        safety_api: Safety,
        tool_runtime_api: ToolRuntime,
        tool_groups_api: ToolGroups,
        vector_io_api: VectorIO,
        persistence_store: KVStore,
    ):
        self.agent_id = agent_id
        self.agent_config = agent_config
        self.tempdir = tempdir
        self.inference_api = inference_api
        self.safety_api = safety_api
        self.vector_io_api = vector_io_api
        self.storage = AgentPersistence(agent_id, persistence_store)
        self.tool_runtime_api = tool_runtime_api
        self.tool_groups_api = tool_groups_api

        ShieldRunnerMixin.__init__(
            self,
            safety_api,
            input_shields=agent_config.input_shields if agent_config.input_shields else [],
            output_shields=agent_config.output_shields if agent_config.output_shields else [],
        )

    def turn_to_messages(self, turn: Turn) -> List[Any]:  # List[Message]
        messages: List[Any] = []  # List[Message]

        # We do not want to keep adding RAG context to the input messages
        # May be this should be a parameter of the agentic instance
        # that can define its behavior in a custom way
        for m in turn.input_messages:
            msg = m.model_copy()
            if isinstance(msg, UserMessage):
                msg.context = None
            messages.append(msg)

        for step in turn.steps:
            if step.step_type == StepType.inference.value:
                messages.append(step.model_response)
            elif step.step_type == StepType.tool_execution.value:
                for response in step.tool_responses:
                    messages.append(
                        ToolResponseMessage(
                            call_id=response.call_id,
                            tool_name=response.tool_name,
                            content=response.content,
                        )
                    )
            elif step.step_type == StepType.shield_call.value:
                if step.violation:
                    # CompletionMessage itself in the ShieldResponse
                    messages.append(
                        CompletionMessage(
                            content=step.violation.user_message,
                            stop_reason=StopReason.end_of_turn,
                        )
                    )
        return messages

    async def create_session(self, name: str) -> str:
        return await self.storage.create_session(name)

    async def get_messages_from_turns(self, turns: List[Turn]) -> List[Any]:  # List[Message]
        messages: List[Any] = []  # List[Message]
        if self.agent_config.instructions != "":
            messages.append(SystemMessage(content=self.agent_config.instructions))

        for turn in turns:
            messages.extend(self.turn_to_messages(turn))
        return messages

    async def create_and_execute_turn(self, request: AgentTurnCreateRequest) -> AsyncGenerator:
        """Create and execute a new turn in an agent session.
        
        This method processes a turn request, executes the agent's logic, and
        yields streaming responses as the turn progresses.
        
        Args:
            request: The turn request containing messages and configuration.
            
        Yields:
            AgentTurnResponseStreamChunk objects as the turn progresses.
            
        Raises:
            ValueError: If the session is not found.
            AssertionError: If streaming is not enabled.
        """
        with tracing.span("create_and_execute_turn") as span:
            span.set_attribute("session_id", request.session_id)
            span.set_attribute("agent_id", self.agent_id)
            span.set_attribute("request", request.model_dump_json())
            assert request.stream is True, "Non-streaming not supported"

            session_info = await self.storage.get_session_info(request.session_id)
            if session_info is None:
                raise ValueError(f"Session {request.session_id} not found")

            turns = await self.storage.get_session_turns(request.session_id)
            messages = await self.get_messages_from_turns(turns)
            messages.extend(request.messages)

            turn_id = str(uuid.uuid4())
            span.set_attribute("turn_id", turn_id)
            start_time = datetime.now().astimezone().isoformat()
            yield AgentTurnResponseStreamChunk(
                event=AgentTurnResponseEvent(
                    payload=AgentTurnResponseTurnStartPayload(
                        turn_id=turn_id,
                    )
                )
            )

            steps = []
            output_message = None
            async for chunk in self.run(
                session_id=request.session_id,
                turn_id=turn_id,
                input_messages=messages,
                sampling_params=SamplingParams(),
                stream=request.stream,
                documents=request.documents,
                toolgroups_for_turn=request.toolgroups,
            ):
                if isinstance(chunk, CompletionMessage):
                    log.info(
                        f"{chunk.role.capitalize()}: {chunk.content}",
                    )
                    output_message = chunk
                    continue

                assert isinstance(chunk, AgentTurnResponseStreamChunk), f"Unexpected type {type(chunk)}"
                event = chunk.event
                if event.payload.event_type == AgentTurnResponseEventType.step_complete.value:
                    steps.append(event.payload.step_details)

                yield chunk

            assert output_message is not None

            turn = Turn(
                turn_id=turn_id,
                session_id=request.session_id,
                input_messages=request.messages,
                output_message=output_message,
                started_at=start_time,
                completed_at=datetime.now().astimezone().isoformat(),
                steps=steps,
            )
            await self.storage.add_turn_to_session(request.session_id, turn)

            if output_message.tool_calls and request.allow_turn_resume:
                chunk = AgentTurnResponseStreamChunk(
                    event=AgentTurnResponseEvent(
                        payload=AgentTurnResponseTurnAwaitingInputPayload(
                            turn=turn,
                        )
                    )
                )
            else:
                chunk = AgentTurnResponseStreamChunk(
                    event=AgentTurnResponseEvent(
                        payload=AgentTurnResponseTurnCompletePayload(
                            turn=turn,
                        )
                    )
                )

            yield chunk

    async def resume_turn(self, request: AgentTurnResumeRequest) -> AsyncGenerator:
        """Resume a turn that was awaiting tool responses.
        
        This method continues a turn that was paused waiting for client-side tool
        responses, processes those responses, and continues the agent's execution.
        
        Args:
            request: The resume request containing tool responses.
            
        Yields:
            AgentTurnResponseStreamChunk objects as the turn progresses.
            
        Raises:
            ValueError: If the session is not found.
            AssertionError: If streaming is not enabled.
        """
        with tracing.span("resume_turn") as span:
            span.set_attribute("agent_id", self.agent_id)
            span.set_attribute("session_id", request.session_id)
            span.set_attribute("turn_id", request.turn_id)
            span.set_attribute("request", request.model_dump_json())
            assert request.stream is True, "Non-streaming not supported"

            session_info = await self.storage.get_session_info(request.session_id)
            if session_info is None:
                raise ValueError(f"Session {request.session_id} not found")

            turns = await self.storage.get_session_turns(request.session_id)
            messages = await self.get_messages_from_turns(turns)
            messages.extend(request.tool_responses)

            last_turn_messages = [
                x for x in messages if isinstance(x, UserMessage) or isinstance(x, ToolResponseMessage)
            ]

            # get the steps from the turn id
            steps = []
            if len(turns) > 0:
                steps = turns[-1].steps

            # mark tool execution step as complete
            # if there's no tool execution in progress step (due to storage, or tool call parsing on client),
            # we'll create a new tool execution step with current time
            in_progress_tool_call_step = await self.storage.get_in_progress_tool_call_step(
                request.session_id, request.turn_id
            )
            now = datetime.now().astimezone().isoformat()
            tool_execution_step = ToolExecutionStep(
                step_id=(in_progress_tool_call_step.step_id if in_progress_tool_call_step else str(uuid.uuid4())),
                turn_id=request.turn_id,
                tool_calls=(in_progress_tool_call_step.tool_calls if in_progress_tool_call_step else []),
                tool_responses=[
                    ToolResponse(
                        call_id=x.call_id,
                        tool_name=x.tool_name,
                        content=x.content,
                    )
                    for x in request.tool_responses
                ],
                completed_at=now,
                started_at=(in_progress_tool_call_step.started_at if in_progress_tool_call_step else now),
            )
            steps.append(tool_execution_step)
            yield AgentTurnResponseStreamChunk(
                event=AgentTurnResponseEvent(
                    payload=AgentTurnResponseStepCompletePayload(
                        step_type=StepType.tool_execution.value,
                        step_id=tool_execution_step.step_id,
                        step_details=tool_execution_step,
                    )
                )
            )

            output_message = None
            async for chunk in self.run(
                session_id=request.session_id,
                turn_id=request.turn_id,
                input_messages=messages,
                sampling_params=SamplingParams() if not hasattr(self.agent_config, 'sampling_params') else self.agent_config.sampling_params,
                stream=request.stream,
            ):
                if isinstance(chunk, CompletionMessage):
                    output_message = chunk
                    continue

                assert isinstance(chunk, AgentTurnResponseStreamChunk), f"Unexpected type {type(chunk)}"
                event = chunk.event
                if event.payload.event_type == AgentTurnResponseEventType.step_complete.value:
                    steps.append(event.payload.step_details)

                yield chunk

            assert output_message is not None

            last_turn_start_time = datetime.now().astimezone().isoformat()
            if len(turns) > 0:
                last_turn_start_time = turns[-1].started_at

            turn = Turn(
                turn_id=request.turn_id,
                session_id=request.session_id,
                input_messages=last_turn_messages,
                output_message=output_message,
                started_at=last_turn_start_time,
                completed_at=datetime.now().astimezone().isoformat(),
                steps=steps,
            )
            await self.storage.add_turn_to_session(request.session_id, turn)

            if output_message.tool_calls:
                chunk = AgentTurnResponseStreamChunk(
                    event=AgentTurnResponseEvent(
                        payload=AgentTurnResponseTurnAwaitingInputPayload(
                            turn=turn,
                        )
                    )
                )
            else:
                chunk = AgentTurnResponseStreamChunk(
                    event=AgentTurnResponseEvent(
                        payload=AgentTurnResponseTurnCompletePayload(
                            turn=turn,
                        )
                    )
                )

            yield chunk

    async def run(
        self,
        session_id: str,
        turn_id: str,
        input_messages: List[Any],  # List[Message]
        sampling_params: SamplingParams,
        stream: bool = False,
        documents: Optional[List[Document]] = None,
        toolgroups_for_turn: Optional[List[str]] = None,
    ) -> AsyncGenerator:
        """Run the agent's core logic for a turn.
        
        This method processes input messages, applies safety shields, executes
        the agent's reasoning, and handles tool calls.
        
        Args:
            session_id: The ID of the session.
            turn_id: The ID of the turn.
            input_messages: List of input messages to process.
            sampling_params: Parameters for controlling model sampling.
            stream: Whether to stream the response.
            documents: Optional documents to provide to the agent.
            toolgroups_for_turn: Optional tool groups to make available for this turn.
            
        Yields:
            AgentTurnResponseStreamChunk objects or CompletionMessage objects.
        """
        # Doing async generators makes downstream code much simpler and everything amenable to
        # streaming. However, it also makes things complicated here because AsyncGenerators cannot
        # return a "final value" for the `yield from` statement. we simulate that by yielding a
        # final boolean (to see whether an exception happened) and then explicitly testing for it.

        if len(self.input_shields) > 0:
            async for res in self.run_multiple_shields_wrapper(
                turn_id, input_messages, self.input_shields, "user-input"
            ):
                if isinstance(res, bool):
                    return
                else:
                    yield res

        async for res in self._run(
            session_id,
            turn_id,
            input_messages,
            sampling_params,
            stream,
            documents,
            toolgroups_for_turn,
        ):
            if isinstance(res, bool):
                return
            elif isinstance(res, CompletionMessage):
                final_response = res
                break
            else:
                yield res

        assert final_response is not None
        # for output shields run on the full input and output combination
        messages = input_messages + [final_response]

        if len(self.output_shields) > 0:
            async for res in self.run_multiple_shields_wrapper(
                turn_id, messages, self.output_shields, "assistant-output"
            ):
                if isinstance(res, bool):
                    return
                else:
                    yield res

        yield final_response

    async def run_multiple_shields_wrapper(
        self,
        turn_id: str,
        messages: List[Any],  # List[Message]
        shields: List[str],
        touchpoint: str,
    ) -> AsyncGenerator:
        """Run multiple safety shields on messages and yield the results.
        
        This method applies a list of safety shields to messages and yields
        streaming responses as the shields are applied.
        
        Args:
            turn_id: The ID of the turn.
            messages: List of messages to check.
            shields: List of shield IDs to apply.
            touchpoint: The point in the conversation to apply shields (e.g., "user-input").
            
        Yields:
            AgentTurnResponseStreamChunk objects or CompletionMessage objects.
        """
        with tracing.span("run_shields") as span:
            span.set_attribute("input", [m.model_dump_json() for m in messages])
            if len(shields) == 0:
                span.set_attribute("output", "no shields")
                return

            step_id = str(uuid.uuid4())
            shield_call_start_time = datetime.now().astimezone().isoformat()
            try:
                yield AgentTurnResponseStreamChunk(
                    event=AgentTurnResponseEvent(
                        payload=AgentTurnResponseStepStartPayload(
                            step_type=StepType.shield_call.value,
                            step_id=step_id,
                            metadata=dict(touchpoint=touchpoint),
                        )
                    )
                )
                await self.run_multiple_shields(messages, shields)

            except SafetyException as e:
                yield AgentTurnResponseStreamChunk(
                    event=AgentTurnResponseEvent(
                        payload=AgentTurnResponseStepCompletePayload(
                            step_type=StepType.shield_call.value,
                            step_id=step_id,
                            step_details=ShieldCallStep(
                                step_id=step_id,
                                turn_id=turn_id,
                                violation=e.violation,
                                started_at=shield_call_start_time,
                                completed_at=datetime.now().astimezone().isoformat(),
                            ),
                        )
                    )
                )
                span.set_attribute("output", e.violation.model_dump_json())

                yield CompletionMessage(
                    content=str(e),
                    stop_reason=StopReason.end_of_turn,
                )
                yield False

            yield AgentTurnResponseStreamChunk(
                event=AgentTurnResponseEvent(
                    payload=AgentTurnResponseStepCompletePayload(
                        step_type=StepType.shield_call.value,
                        step_id=step_id,
                        step_details=ShieldCallStep(
                            step_id=step_id,
                            turn_id=turn_id,
                            violation=None,
                            started_at=shield_call_start_time,
                            completed_at=datetime.now().astimezone().isoformat(),
                        ),
                    )
                )
            )
            span.set_attribute("output", "no violations")

    async def _process_toolgroups(
        self,
        toolgroups_for_turn: Optional[List[str]] = None
    ) -> Tuple[Dict[str, Dict[str, Any]], set]:
        """
        Process toolgroups from agent config and turn request.
        
        Args:
            toolgroups_for_turn: Optional list of toolgroups specified for this turn
            
        Returns:
            Tuple containing:
            - toolgroup_args: Dictionary mapping toolgroup names to their arguments
            - toolgroups: Set of toolgroup names
        """
        toolgroup_args = {}
        toolgroups = set()
        
        # Process toolgroups from agent config
        for toolgroup in (self.agent_config.toolgroups or []):
            if isinstance(toolgroup, AgentToolGroupWithArgs):
                toolgroups.add(toolgroup.name)
                toolgroup_args[toolgroup.name] = toolgroup.args
            else:
                toolgroups.add(toolgroup)
                
        # Process toolgroups specified for this turn
        if toolgroups_for_turn:
            for toolgroup in toolgroups_for_turn:
                if isinstance(toolgroup, AgentToolGroupWithArgs):
                    toolgroups.add(toolgroup.name)
                    toolgroup_args[toolgroup.name] = toolgroup.args
                else:
                    toolgroups.add(toolgroup)
                    
        return toolgroup_args, toolgroups
        
    async def _process_rag_tool_query(
        self,
        session_id: str,
        turn_id: str,
        input_messages: List[Any],  # List[Message]
        toolgroup_args: Dict[str, Dict[str, Any]]
    ) -> AsyncGenerator[AgentTurnResponseStreamChunk, None]:
        """
        Process RAG tool query and update input messages with retrieved context.
        
        Args:
            session_id: The ID of the session
            turn_id: The ID of the turn
            input_messages: List of input messages
            toolgroup_args: Dictionary mapping toolgroup names to their arguments
            
        Yields:
            AgentTurnResponseStreamChunk objects
        """
        with tracing.span(MEMORY_QUERY_TOOL) as span:
            step_id = str(uuid.uuid4())
            yield AgentTurnResponseStreamChunk(
                event=AgentTurnResponseEvent(
                    payload=AgentTurnResponseStepStartPayload(
                        step_type=StepType.tool_execution.value,
                        step_id=step_id,
                    )
                )
            )

            args = toolgroup_args.get(RAG_TOOL_GROUP, {})
            vector_db_ids = args.get("vector_db_ids", [])
            query_config = args.get("query_config")
            if query_config:
                query_config = TypeAdapter(RAGQueryConfig).validate_python(query_config)
            else:
                # handle someone passing an empty dict
                query_config = RAGQueryConfig()

            session_info = await self.storage.get_session_info(session_id)

            # if the session has a memory bank id, let the memory tool use it
            if session_info and session_info.vector_db_id:
                vector_db_ids.append(session_info.vector_db_id)

            yield AgentTurnResponseStreamChunk(
                event=AgentTurnResponseEvent(
                    payload=AgentTurnResponseStepProgressPayload(
                        step_type=StepType.tool_execution.value,
                        step_id=step_id,
                        delta=ToolCallDelta(
                            parse_status=ToolCallParseStatus.succeeded,
                            tool_call=ToolCall(
                                call_id="",
                                tool_name=MEMORY_QUERY_TOOL,
                                arguments={},
                            ),
                        ),
                    )
                )
            )
            result = await self.tool_runtime_api.rag_tool.query(
                content=concat_interleaved_content([msg.content for msg in input_messages]),
                vector_db_ids=vector_db_ids,
                query_config=query_config,
            )
            retrieved_context = result.content

            yield AgentTurnResponseStreamChunk(
                event=AgentTurnResponseEvent(
                    payload=AgentTurnResponseStepCompletePayload(
                        step_type=StepType.tool_execution.value,
                        step_id=step_id,
                        step_details=ToolExecutionStep(
                            step_id=step_id,
                            turn_id=turn_id,
                            tool_calls=[
                                ToolCall(
                                    call_id="",
                                    tool_name=MEMORY_QUERY_TOOL,
                                    arguments={},
                                )
                            ],
                            tool_responses=[
                                ToolResponse(
                                    call_id="",
                                    tool_name=MEMORY_QUERY_TOOL,
                                    content=retrieved_context or [],
                                    metadata=result.metadata,
                                )
                            ],
                        ),
                    )
                )
            )
            span.set_attribute("input", [m.model_dump_json() for m in input_messages])
            span.set_attribute("output", retrieved_context)
            span.set_attribute("tool_name", MEMORY_QUERY_TOOL)

            # append retrieved_context to the last user message
            for message in input_messages[::-1]:
                if isinstance(message, UserMessage):
                    message.context = retrieved_context
                    break
    
    async def _process_inference_step(
        self,
        turn_id: str,
        input_messages: List[Any],  # List[Message]
        tool_defs: Dict[str, ToolDefinition],
        tool_to_group: Dict[str, str],
        sampling_params: SamplingParams,
        stream: bool = False
    ) -> Tuple[CompletionMessage, str, StopReason, AsyncGenerator[AgentTurnResponseStreamChunk, None]]:
        """
        Process inference step and get model response.
        
        Args:
            turn_id: The ID of the turn
            input_messages: List of input messages
            tool_defs: Dictionary mapping tool names to their definitions
            tool_to_group: Dictionary mapping tool names to their group names
            sampling_params: Sampling parameters for the model
            stream: Whether to stream the response
            
        Returns:
            Tuple containing:
            - The completion message from the model
            - The ID of the step
        """
        step_id = str(uuid.uuid4())
        inference_start_time = datetime.now().astimezone().isoformat()
        # Create a generator for yielding inference progress
        inference_chunks = []
        inference_chunks.append(AgentTurnResponseStreamChunk(
            event=AgentTurnResponseEvent(
                payload=AgentTurnResponseStepStartPayload(
                    step_type=StepType.inference.value,
                    step_id=step_id,
                )
            )
        ))

        tool_calls = []
        content = ""
        stop_reason = None

        with tracing.span("inference") as span:
            async for chunk in await self.inference_api.chat_completion(
                self.agent_config.model,
                input_messages,
                tools=[
                    tool for tool in tool_defs.values() if tool_to_group.get(tool.tool_name, None) != RAG_TOOL_GROUP
                ],
                tool_prompt_format=self.agent_config.tool_config.tool_prompt_format if self.agent_config.tool_config else None,
                response_format=self.agent_config.response_format if hasattr(self.agent_config, 'response_format') else None,
                stream=True,
                sampling_params=sampling_params,
                tool_config=self.agent_config.tool_config,
            ):
                event = chunk.event
                if event.event_type == ChatCompletionResponseEventType.start:
                    continue
                elif event.event_type == ChatCompletionResponseEventType.complete:
                    stop_reason = StopReason.end_of_turn
                    continue

                delta = event.delta
                if delta.type == "tool_call":
                    if delta.parse_status == ToolCallParseStatus.succeeded:
                        tool_calls.append(delta.tool_call)
                    elif delta.parse_status == ToolCallParseStatus.failed:
                        # If we cannot parse the tools, set the content to the unparsed raw text
                        content = delta.tool_call
                    if stream:
                        # Add to inference chunks instead of yielding directly
                        inference_chunks.append(AgentTurnResponseStreamChunk(
                            event=AgentTurnResponseEvent(
                                payload=AgentTurnResponseStepProgressPayload(
                                    step_type=StepType.inference.value,
                                    step_id=step_id,
                                    delta=delta,
                                )
                            )
                        ))

                elif delta.type == "text":
                    content += delta.text
                    if stream and event.stop_reason is None:
                        # Add to inference chunks instead of yielding directly
                        inference_chunks.append(AgentTurnResponseStreamChunk(
                            event=AgentTurnResponseEvent(
                                payload=AgentTurnResponseStepProgressPayload(
                                    step_type=StepType.inference.value,
                                    step_id=step_id,
                                    delta=delta,
                                )
                            )
                        ))
                else:
                    raise ValueError(f"Unexpected delta type {type(delta)}")

                if event.stop_reason is not None:
                    stop_reason = event.stop_reason
            span.set_attribute("stop_reason", stop_reason)
            span.set_attribute("input", [m.model_dump_json() for m in input_messages])
            span.set_attribute("output", f"content: {content} tool_calls: {tool_calls}")

        stop_reason = stop_reason or StopReason.out_of_tokens

        # If tool calls are parsed successfully,
        # if content is not made null the tool call str will also be in the content
        # and tokens will have tool call syntax included twice
        if tool_calls:
            content = ""

        message = CompletionMessage(
            content=content,
            stop_reason=stop_reason,
            tool_calls=tool_calls,
        )
        
        # Add completion chunk
        inference_chunks.append(AgentTurnResponseStreamChunk(
            event=AgentTurnResponseEvent(
                payload=AgentTurnResponseStepCompletePayload(
                    step_type=StepType.inference.value,
                    step_id=step_id,
                    step_details=InferenceStep(
                        # somewhere deep, we are re-assigning message or closing over some
                        # variable which causes message to mutate later on. fix with a
                        # `deepcopy` for now, but this is symptomatic of a deeper issue.
                        step_id=step_id,
                        turn_id=turn_id,
                        model_response=copy.deepcopy(message),
                        started_at=inference_start_time,
                        completed_at=datetime.now().astimezone().isoformat(),
                    ),
                )
            )
        ))
        
        # Create an async generator from the chunks
        async def inference_generator():
            for chunk in inference_chunks:
                yield chunk
            
        # Return the message, step_id, stop_reason, and the inference generator
        return message, step_id, stop_reason, inference_generator()
    
    # This method is no longer needed as we're returning the generator directly from _process_inference_step
    
    async def _process_tool_execution(
        self,
        session_id: str,
        turn_id: str,
        message: CompletionMessage,
        client_tools: Dict[str, Any],
        toolgroup_args: Dict[str, Dict[str, Any]],
        tool_to_group: Dict[str, str]
    ) -> Tuple[AsyncGenerator[AgentTurnResponseStreamChunk, None], Optional[ToolResponseMessage]]:
        """
        Process tool execution step.
        
        Args:
            session_id: The ID of the session
            turn_id: The ID of the turn
            message: The completion message from the model
            client_tools: Dictionary mapping client tool names to their definitions
            toolgroup_args: Dictionary mapping toolgroup names to their arguments
            tool_to_group: Dictionary mapping tool names to their group names
            
        Yields:
            AgentTurnResponseStreamChunk objects and the result message
        """
        # 1. Start the tool execution step and progress
        step_id = str(uuid.uuid4())
        
        # Create a list for tool execution chunks
        tool_execution_chunks = []
        tool_execution_chunks.append(AgentTurnResponseStreamChunk(
            event=AgentTurnResponseEvent(
                payload=AgentTurnResponseStepStartPayload(
                    step_type=StepType.tool_execution.value,
                    step_id=step_id,
                )
            )
        ))
        
        # Ensure tool_calls exists and has at least one element
        if not message.tool_calls or len(message.tool_calls) == 0:
            raise ValueError("No tool calls found in message")
            
        tool_call = message.tool_calls[0]
        
        # Add progress chunk
        tool_execution_chunks.append(AgentTurnResponseStreamChunk(
            event=AgentTurnResponseEvent(
                payload=AgentTurnResponseStepProgressPayload(
                    step_type=StepType.tool_execution.value,
                    step_id=step_id,
                    tool_call=tool_call,
                    delta=ToolCallDelta(
                        parse_status=ToolCallParseStatus.in_progress,
                        tool_call=tool_call,
                    ),
                )
            )
        ))

        # If tool is a client tool, yield CompletionMessage and return
        if tool_call.tool_name in client_tools:
            await self.storage.set_in_progress_tool_call_step(
                session_id,
                turn_id,
                ToolExecutionStep(
                    step_id=step_id,
                    turn_id=turn_id,
                    tool_calls=[tool_call],
                    tool_responses=[],
                    started_at=datetime.now().astimezone().isoformat(),
                ),
            )
            # Create an async generator from the chunks
            async def client_tool_generator():
                for chunk in tool_execution_chunks:
                    yield chunk
                yield message
                
            # For client tools, we just return the generator and no result message
            return client_tool_generator(), None

        # If tool is a builtin server tool, execute it
        tool_name = tool_call.tool_name
        if isinstance(tool_name, BuiltinTool):
            tool_name = tool_name.value
        with tracing.span(
            "tool_execution",
            {
                "tool_name": tool_name,
                "input": message.model_dump_json(),
            },
        ) as span:
            tool_execution_start_time = datetime.now().astimezone().isoformat()
            tool_result = await execute_tool_call_maybe(
                self.tool_runtime_api,
                session_id,
                tool_call,
                toolgroup_args,
                tool_to_group,
            )
            if tool_result.content is None:
                raise ValueError(
                    f"Tool call result (id: {tool_call.call_id}, name: {tool_call.tool_name}) does not have any content"
                )
            result_messages = [
                ToolResponseMessage(
                    call_id=tool_call.call_id,
                    tool_name=tool_call.tool_name,
                    content=tool_result.content,
                )
            ]
            assert len(result_messages) == 1, "Currently not supporting multiple messages"
            result_message = result_messages[0]
            span.set_attribute("output", result_message.model_dump_json())

            # Add completion chunk
            tool_execution_chunks.append(AgentTurnResponseStreamChunk(
                event=AgentTurnResponseEvent(
                    payload=AgentTurnResponseStepCompletePayload(
                        step_type=StepType.tool_execution.value,
                        step_id=step_id,
                        step_details=ToolExecutionStep(
                            step_id=step_id,
                            turn_id=turn_id,
                            tool_calls=[tool_call],
                            tool_responses=[
                                ToolResponse(
                                    call_id=result_message.call_id,
                                    tool_name=result_message.tool_name,
                                    content=result_message.content,
                                    metadata=tool_result.metadata,
                                )
                            ],
                            started_at=tool_execution_start_time,
                            completed_at=datetime.now().astimezone().isoformat(),
                        ),
                    )
                )
            ))
        
        # Create an async generator from the chunks
        async def server_tool_generator():
            for chunk in tool_execution_chunks:
                yield chunk
                
        # Return the generator and result message
        return server_tool_generator(), result_message
    
    async def _run(
        self,
        session_id: str,
        turn_id: str,
        input_messages: List[Any],  # List[Message]
        sampling_params: SamplingParams,
        stream: bool = False,
        documents: Optional[List[Document]] = None,
        toolgroups_for_turn: Optional[List[str]] = None,
    ) -> AsyncGenerator:
        """Internal implementation of the agent's core logic.
        
        This method handles the details of processing input messages, executing
        inference steps, handling tool calls, and managing the agent's state.
        
        Args:
            session_id: The ID of the session.
            turn_id: The ID of the turn.
            input_messages: List of input messages to process.
            sampling_params: Parameters for controlling model sampling.
            stream: Whether to stream the response.
            documents: Optional documents to provide to the agent.
            toolgroups_for_turn: Optional tool groups to make available for this turn.
            
        Yields:
            AgentTurnResponseStreamChunk objects or CompletionMessage objects.
        """
        # TODO: simplify all of this code, it can be simpler
        toolgroup_args, toolgroups = await self._process_toolgroups(toolgroups_for_turn)

        tool_defs, tool_to_group = await self._get_tool_defs(toolgroups_for_turn)
        if documents:
            await self.handle_documents(session_id, documents, input_messages, tool_defs)

        if RAG_TOOL_GROUP in toolgroups and len(input_messages) > 0:
            # Process RAG tool query and update input messages with retrieved context
            async for chunk in self._process_rag_tool_query(
                session_id, 
                turn_id, 
                input_messages, 
                toolgroup_args
            ):
                yield chunk

        output_attachments = []

        n_iter = 0
        # Build a map of custom tools to their definitions for faster lookup
        client_tools = {}
        for tool in (self.agent_config.client_tools or []):
            client_tools[tool.name] = tool
        while True:
            # Process inference step and get model response
            message, step_id, current_stop_reason, inference_generator = await self._process_inference_step(
                turn_id,
                input_messages,
                tool_defs,
                tool_to_group,
                sampling_params,
                stream
            )
            
            # Yield the message from the inference step
            async for chunk in inference_generator:
                yield chunk

            if n_iter >= (self.agent_config.max_infer_iters or 10):
                log.info("Done with MAX iterations, exiting.")
                yield message
                break

            if current_stop_reason == StopReason.out_of_tokens:
                log.info("Out of token budget, exiting.")
                yield message
                break

            if not message.tool_calls or len(message.tool_calls) == 0:
                if current_stop_reason == StopReason.end_of_turn:
                    # TODO: UPDATE RETURN TYPE TO SEND A TUPLE OF (MESSAGE, ATTACHMENTS)
                    if len(output_attachments) > 0:
                        if isinstance(message.content, list):
                            message.content += output_attachments
                        else:
                            message.content = [message.content] + output_attachments
                    yield message
                else:
                    log.info(f"Partial message: {str(message)}")
                    input_messages = input_messages + [message]
            else:
                log.info(f"{str(message)}")
                # Process tool execution step
                tool_chunks, result_message = await self._process_tool_execution(
                    session_id,
                    turn_id,
                    message,
                    client_tools,
                    toolgroup_args,
                    tool_to_group
                )
                
                if tool_chunks:
                    async for chunk in tool_chunks:
                        yield chunk

                # TODO: add tool-input touchpoint and a "start" event for this step also
                # but that needs a lot more refactoring of Tool code potentially

                if result_message and (out_attachment := _interpret_content_as_attachment(result_message.content)):
                    # NOTE: when we push this message back to the model, the model may ignore the
                    # attached file path etc. since the model is trained to only provide a user message
                    # with the summary. We keep all generated attachments and then attach them to final message
                    output_attachments.append(out_attachment)

                if result_message:
                    input_messages = input_messages + [message, result_message]
                else:
                    input_messages = input_messages + [message]

            n_iter += 1

    async def _get_tool_defs(
        self, toolgroups_for_turn: Optional[List[Any]] = None  # List[AgentToolGroup]
    ) -> Tuple[Dict[str, ToolDefinition], Dict[str, str]]:
        """Get tool definitions for the agent.
        
        This method retrieves tool definitions from tool groups and maps
        tool names to their groups.
        
        Args:
            toolgroups_for_turn: Optional tool groups to include for this turn.
            
        Returns:
            A tuple containing:
            - A dictionary mapping tool names to their definitions.
            - A dictionary mapping tool names to their group names.
        """
        # Determine which tools to include
        agent_config_toolgroups = set(
            (toolgroup.name if isinstance(toolgroup, AgentToolGroupWithArgs) else toolgroup)
            for toolgroup in (self.agent_config.toolgroups or [])
        )
        toolgroups_for_turn_set = (
            agent_config_toolgroups
            if toolgroups_for_turn is None
            else {
                (toolgroup.name if isinstance(toolgroup, AgentToolGroupWithArgs) else toolgroup)
                for toolgroup in toolgroups_for_turn
            }
        )

        tool_def_map = {}
        tool_to_group = {}

        for tool_def in (self.agent_config.client_tools or []):
            if tool_def_map.get(tool_def.name, None):
                raise ValueError(f"Tool {tool_def.name} already exists")
            tool_def_map[tool_def.name] = ToolDefinition(
                tool_name=tool_def.name,
                description=tool_def.description,
                parameters={
                    param.name: ToolParamDefinition(
                        param_type=param.parameter_type,
                        description=param.description,
                        required=param.required,
                        default=param.default,
                    )
                    for param in (tool_def.parameters or [])
                },
            )
            tool_to_group[tool_def.name] = "__client_tools__"
        for toolgroup_name in agent_config_toolgroups:
            if toolgroup_name not in toolgroups_for_turn_set:
                continue
            tools = await self.tool_groups_api.list_tools(toolgroup_id=toolgroup_name)
            for tool_def in tools.data:
                if toolgroup_name.startswith("builtin") and toolgroup_name != RAG_TOOL_GROUP:
                    tool_name = tool_def.identifier
                    built_in_type = BuiltinTool.brave_search
                    if tool_name == "web_search":
                        built_in_type = BuiltinTool.brave_search
                    else:
                        built_in_type = BuiltinTool(tool_name)

                    if tool_def_map.get(built_in_type, None):
                        raise ValueError(f"Tool {built_in_type} already exists")

                    tool_def_map[built_in_type] = ToolDefinition(tool_name=built_in_type)
                    tool_to_group[built_in_type] = tool_def.toolgroup_id
                    continue

                if tool_def_map.get(tool_def.identifier, None):
                    raise ValueError(f"Tool {tool_def.identifier} already exists")
                tool_def_map[tool_def.identifier] = ToolDefinition(
                    tool_name=tool_def.identifier,
                    description=tool_def.description,
                    parameters={
                        param.name: ToolParamDefinition(
                            param_type=param.parameter_type,
                            description=param.description,
                            required=param.required,
                            default=param.default,
                        )
                        for param in (tool_def.parameters or [])
                    },
                )
                tool_to_group[tool_def.identifier] = tool_def.toolgroup_id

        return tool_def_map, tool_to_group

    async def handle_documents(
        self,
        session_id: str,
        documents: List[Document],
        input_messages: List[Any],  # List[Message]
        tool_defs: Dict[str, ToolDefinition],
    ) -> None:
        """Process documents provided to the agent.
        
        This method handles documents provided to the agent, loading their content
        and adding them to the session's vector database if needed.
        
        Args:
            session_id: The ID of the session.
            documents: List of documents to process.
            input_messages: List of input messages to update with document content.
            tool_defs: Dictionary of tool definitions.
            
        Returns:
            None
        """
        memory_tool = tool_defs.get(MEMORY_QUERY_TOOL, None)
        code_interpreter_tool = tool_defs.get(BuiltinTool.code_interpreter, None)
        content_items = []
        url_items = []
        pattern = re.compile("^(https?://|file://|data:)")
        for d in documents:
            if isinstance(d.content, URL):
                url_items.append(d.content)
            elif pattern.match(d.content):
                url_items.append(URL(uri=d.content))
            else:
                content_items.append(d)

        # Save the contents to a tempdir and use its path as a URL if code interpreter is present
        if code_interpreter_tool:
            for c in content_items:
                temp_file_path = os.path.join(self.tempdir, f"{make_random_string()}.txt")
                with open(temp_file_path, "w") as temp_file:
                    temp_file.write(c.content)
                url_items.append(URL(uri=f"file://{temp_file_path}"))

        if memory_tool and code_interpreter_tool:
            # if both memory and code_interpreter are available, we download the URLs
            # and attach the data to the last message.
            msg = await attachment_message(self.tempdir, url_items)
            input_messages.append(msg)
            # Since memory is present, add all the data to the memory bank
            await self.add_to_session_vector_db(session_id, documents)
        elif code_interpreter_tool:
            # if only code_interpreter is available, we download the URLs to a tempdir
            # and attach the path to them as a message to inference with the
            # assumption that the model invokes the code_interpreter tool with the path
            msg = await attachment_message(self.tempdir, url_items)
            input_messages.append(msg)
        elif memory_tool:
            # if only memory is available, we load the data from the URLs and content items to the memory bank
            await self.add_to_session_vector_db(session_id, documents)
        else:
            # if no memory or code_interpreter tool is available,
            # we try to load the data from the URLs and content items as a message to inference
            # and add it to the last message's context
            input_messages[-1].context = "\n".join(
                [doc.content for doc in content_items] + await load_data_from_urls(url_items)
            )

    async def _ensure_vector_db(self, session_id: str) -> str:
        """Ensure a vector database exists for the session.
        
        This method checks if a vector database exists for the session and
        creates one if it doesn't.
        
        Args:
            session_id: The ID of the session.
            
        Returns:
            The ID of the vector database.
        """
        """
        Ensure a vector database exists for the session, creating one if needed.
        
        Args:
            session_id: The ID of the session
            
        Returns:
            The vector database ID
            
        Raises:
            ValueError: If the session is not found
            RuntimeError: If vector database creation fails
        """
        try:
            if not session_id:
                log.error("Missing session_id in _ensure_vector_db")
                raise ValueError("Session ID is required")
                
            # Get session info
            try:
                session_info = await self.storage.get_session_info(session_id)
                if session_info is None:
                    log.error(f"Session {session_id} not found")
                    raise ValueError(f"Session {session_id} not found")
            except Exception as e:
                log.error(f"Error retrieving session info for {session_id}: {e}")
                raise RuntimeError(f"Failed to retrieve session info: {e}")
            
            # Return existing vector DB ID if available
            if session_info.vector_db_id is not None:
                return session_info.vector_db_id
                
            # Create a new vector DB
            vector_db_id = f"vector_db_{session_id}"
            log.info(f"Creating new vector database with ID: {vector_db_id}")
            
            try:
                # This is a workaround for the type checking issue
                # Cast to Any to bypass type checking for the register_vector_db method
                from typing import cast, Any
                vector_io_api = cast(Any, self.vector_io_api)
                await vector_io_api.register_vector_db(
                    vector_db_id=vector_db_id,
                    embedding_model="all-MiniLM-L6-v2",
                )
            except Exception as e:
                log.error(f"Error registering vector DB {vector_db_id}: {e}")
                raise RuntimeError(f"Failed to register vector database: {e}")
                
            try:
                await self.storage.add_vector_db_to_session(session_id, vector_db_id)
                log.info(f"Successfully added vector DB {vector_db_id} to session {session_id}")
            except Exception as e:
                log.error(f"Error adding vector DB to session {session_id}: {e}")
                # Try to clean up the created vector DB
                try:
                    await vector_io_api.unregister_vector_db(vector_db_id=vector_db_id)
                except Exception as cleanup_error:
                    log.error(f"Failed to clean up vector DB after error: {cleanup_error}")
                raise RuntimeError(f"Failed to add vector database to session: {e}")
                
            return vector_db_id
            
        except ValueError:
            # Re-raise ValueError exceptions
            raise
        except Exception as e:
            log.error(f"Unexpected error in _ensure_vector_db: {e}")
            raise RuntimeError(f"Failed to ensure vector database: {e}")

    async def add_to_session_vector_db(self, session_id: str, data: List[Document]) -> None:
        """
        Add documents to the session's vector database.
        
        Args:
            session_id: The ID of the session
            data: List of documents to add
            
        Raises:
            ValueError: If session_id is invalid or data is empty
            RuntimeError: If adding documents to the vector database fails
        """
        try:
            if not session_id:
                log.error("Missing session_id in add_to_session_vector_db")
                raise ValueError("Session ID is required")
                
            if not data:
                log.warning(f"No documents provided to add to session {session_id}")
                return
                
            # Get or create the vector database for this session
            try:
                vector_db_id = await self._ensure_vector_db(session_id)
                log.info(f"Using vector DB {vector_db_id} for session {session_id}")
            except Exception as e:
                log.error(f"Error ensuring vector DB for session {session_id}: {e}")
                raise
                
            # Convert documents to RAG format
            try:
                documents = []
                for a in data:
                    try:
                        doc = RAGDocument(
                            document_id=str(uuid.uuid4()),
                            content=a.content,
                            mime_type=a.mime_type,
                            metadata={},
                        )
                        documents.append(doc)
                    except Exception as doc_error:
                        log.error(f"Error converting document to RAG format: {doc_error}")
                        # Continue with other documents
            except Exception as e:
                log.error(f"Error preparing documents for vector DB: {e}")
                raise RuntimeError(f"Failed to prepare documents: {e}")
                
            if not documents:
                log.warning("No valid documents to insert into vector DB")
                return
                
            # Insert documents into the vector database
            try:
                await self.tool_runtime_api.rag_tool.insert(
                    documents=documents,
                    vector_db_id=vector_db_id,
                    chunk_size_in_tokens=512,
                )
                log.info(f"Successfully inserted {len(documents)} documents into vector DB {vector_db_id}")
            except Exception as e:
                log.error(f"Error inserting documents into vector DB {vector_db_id}: {e}")
                raise RuntimeError(f"Failed to insert documents into vector database: {e}")
                
        except (ValueError, RuntimeError):
            # Re-raise these exceptions
            raise
        except Exception as e:
            log.error(f"Unexpected error in add_to_session_vector_db: {e}")
            raise RuntimeError(f"Failed to add documents to session vector database: {e}")


async def load_data_from_urls(urls: List[URL]) -> List[str]:
    """
    Load data from a list of URLs.
    
    Args:
        urls: List of URLs to load data from
        
    Returns:
        List of string data loaded from the URLs
    """
    data = []
    for url in urls:
        try:
            if not url or not hasattr(url, 'uri') or not url.uri:
                log.warning(f"Invalid URL object: {url}")
                continue
                
            uri = url.uri
            if uri.startswith("file://"):
                filepath = uri[len("file://") :]
                try:
                    with open(filepath, "r") as f:
                        data.append(f.read())
                except FileNotFoundError:
                    log.error(f"File not found: {filepath}")
                except PermissionError:
                    log.error(f"Permission denied when reading file: {filepath}")
                except Exception as e:
                    log.error(f"Error reading file {filepath}: {e}")
            elif uri.startswith("http"):
                try:
                    async with httpx.AsyncClient(timeout=30.0) as client:
                        r = await client.get(uri)
                        r.raise_for_status()  # Raise exception for 4XX/5XX responses
                        resp = r.text
                        data.append(resp)
                except httpx.TimeoutException:
                    log.error(f"Timeout when fetching URL: {uri}")
                except httpx.HTTPStatusError as e:
                    log.error(f"HTTP error when fetching URL {uri}: {e.response.status_code}")
                except httpx.RequestError as e:
                    log.error(f"Request error when fetching URL {uri}: {e}")
                except Exception as e:
                    log.error(f"Error fetching URL {uri}: {e}")
            else:
                log.warning(f"Unsupported URL scheme: {uri}")
        except Exception as e:
            log.error(f"Unexpected error processing URL {url}: {e}")
            
    return data


async def attachment_message(tempdir: str, urls: List[URL]) -> ToolResponseMessage:
    """
    Create a tool response message with file attachments from URLs.
    
    Args:
        tempdir: Directory to store downloaded files
        urls: List of URLs to process
        
    Returns:
        A ToolResponseMessage with file paths
        
    Raises:
        ValueError: If tempdir is invalid or URLs are unsupported
        RuntimeError: If file operations fail
    """
    content = []

    if not tempdir:
        log.error("Missing tempdir in attachment_message")
        raise ValueError("Temporary directory is required")
        
    if not os.path.isdir(tempdir):
        log.error(f"Invalid temporary directory: {tempdir}")
        raise ValueError(f"Invalid temporary directory: {tempdir}")
        
    if not urls:
        log.warning("No URLs provided to attachment_message")
        # Return an empty message rather than raising an exception
        return ToolResponseMessage(
            call_id="",
            tool_name=BuiltinTool.code_interpreter,
            content=content,
        )

    for url in urls:
        try:
            if not url or not hasattr(url, 'uri') or not url.uri:
                log.warning(f"Invalid URL object: {url}")
                continue
                
            uri = url.uri
            
            if uri.startswith("file://"):
                filepath = uri[len("file://") :]
                # Verify the file exists
                if not os.path.exists(filepath):
                    log.error(f"File not found: {filepath}")
                    continue
                    
            elif uri.startswith("http"):
                try:
                    path = urlparse(uri).path
                    basename = os.path.basename(path) or "downloaded_file"
                    filepath = os.path.join(tempdir, f"{make_random_string()}_{basename}")
                    log.info(f"Downloading {url} -> {filepath}")

                    async with httpx.AsyncClient(timeout=30.0) as client:
                        r = await client.get(uri)
                        r.raise_for_status()  # Raise exception for 4XX/5XX responses
                        resp = r.text
                        
                        try:
                            with open(filepath, "w") as fp:
                                fp.write(resp)
                        except PermissionError:
                            log.error(f"Permission denied when writing to file: {filepath}")
                            continue
                        except Exception as file_error:
                            log.error(f"Error writing to file {filepath}: {file_error}")
                            continue
                            
                except httpx.TimeoutException:
                    log.error(f"Timeout when fetching URL: {uri}")
                    continue
                except httpx.HTTPStatusError as e:
                    log.error(f"HTTP error when fetching URL {uri}: {e.response.status_code}")
                    continue
                except httpx.RequestError as e:
                    log.error(f"Request error when fetching URL {uri}: {e}")
                    continue
                except Exception as download_error:
                    log.error(f"Error downloading from URL {uri}: {download_error}")
                    continue
            else:
                log.warning(f"Unsupported URL scheme: {uri}")
                continue

            content.append(TextContentItem(text=f'# There is a file accessible to you at "{filepath}"\n'))
            
        except Exception as e:
            log.error(f"Unexpected error processing URL {url}: {e}")
            # Continue with other URLs

    return ToolResponseMessage(
        call_id="",
        tool_name=BuiltinTool.code_interpreter,
        content=content,
    )


async def execute_tool_call_maybe(
    tool_runtime_api: ToolRuntime,
    session_id: str,
    tool_call: ToolCall,
    toolgroup_args: Dict[str, Dict[str, Any]],
    tool_to_group: Dict[str, str],
) -> ToolInvocationResult:
    """Execute a tool call with appropriate arguments.
    
    This function executes a tool call, handling different tool types and
    passing appropriate arguments based on the tool's group.
    
    Args:
        tool_runtime_api: The tool runtime API to use for execution.
        session_id: The ID of the session.
        tool_call: The tool call to execute.
        toolgroup_args: Dictionary mapping tool group names to their arguments.
        tool_to_group: Dictionary mapping tool names to their group names.
        
    Returns:
        The result of the tool invocation.
        
    Raises:
        ValueError: If the tool name is not recognized.
    """
    """
    Execute a tool call with error handling.
    
    Args:
        tool_runtime_api: The tool runtime API
        session_id: The ID of the session
        tool_call: The tool call to execute
        toolgroup_args: Dictionary of tool group arguments
        tool_to_group: Mapping of tool names to their groups
        
    Returns:
        The result of the tool invocation
        
    Raises:
        ValueError: If tool parameters are invalid
        RuntimeError: If tool execution fails
    """
    try:
        with tracing.span("execute_tool_call") as span:
            # Validate input parameters
            if not tool_runtime_api:
                log.error("Missing tool_runtime_api in execute_tool_call_maybe")
                raise ValueError("Tool runtime API is required")
                
            if not session_id:
                log.error("Missing session_id in execute_tool_call_maybe")
                raise ValueError("Session ID is required")
                
            if not tool_call:
                log.error("Missing tool_call in execute_tool_call_maybe")
                raise ValueError("Tool call is required")
                
            name = tool_call.tool_name
            span.set_attribute("tool_name", str(name))
            
            # Validate tool exists in a group
            group_name = tool_to_group.get(name, None)
            if group_name is None:
                log.error(f"Tool {name} not found in any tool group")
                raise ValueError(f"Tool {name} not found in any tool group")
                
            # Get the arguments generated by the model and augment with toolgroup arg overrides
            tool_call_args = {}
            if tool_call.arguments:
                tool_call_args = tool_call.arguments.copy()
            
            # Add toolgroup arguments if available
            group_args = toolgroup_args.get(group_name, {})
            if group_args:
                tool_call_args.update(group_args)
                
            # Handle builtin tools
            tool_name = name
            if isinstance(name, BuiltinTool):
                if name == BuiltinTool.brave_search:
                    tool_name = WEB_SEARCH_TOOL
                else:
                    tool_name = name.value
                    
            log.info(f"Invoking tool: {tool_name} with args: {tool_call_args}")
            
            # Invoke the tool
            try:
                result = await tool_runtime_api.invoke_tool(
                    tool_name=tool_name,
                    kwargs=dict(
                        session_id=session_id,
                        **tool_call_args,
                    ),
                )
                return result
            except Exception as e:
                log.error(f"Error invoking tool {tool_name}: {e}")
                # Create a fallback result with error information
                from llama_stack.apis.tools import ToolInvocationResult
                return ToolInvocationResult(
                    content=f"Error invoking tool {tool_name}: {str(e)}",
                    metadata={"error": str(e), "tool_name": tool_name}
                )
                
    except Exception as e:
        log.error(f"Unexpected error in execute_tool_call_maybe: {e}")
        # Create a fallback result with error information
        from llama_stack.apis.tools import ToolInvocationResult
        return ToolInvocationResult(
            content=f"An unexpected error occurred: {str(e)}",
            metadata={"error": str(e)}
        )


def _interpret_content_as_attachment(
    content: str,
) -> Optional[Attachment]:
    """
    Extract attachment information from content string.
    
    Args:
        content: String content to parse for attachment information
        
    Returns:
        Attachment object if found, None otherwise
    """
    if not content:
        return None
        
    try:
        match = re.search(TOOLS_ATTACHMENT_KEY_REGEX, content)
        if not match:
            return None
            
        snippet = match.group(1)
        if not snippet:
            log.warning("Empty attachment data in content")
            return None
            
        try:
            data = json.loads(snippet)
        except json.JSONDecodeError as e:
            log.error(f"Error parsing attachment JSON: {e}")
            return None
            
        # Validate required fields
        if "filepath" not in data:
            log.error("Missing filepath in attachment data")
            return None
            
        if "mimetype" not in data:
            log.warning("Missing mimetype in attachment data, using default")
            mimetype = "application/octet-stream"
        else:
            mimetype = data["mimetype"]
            
        # Verify file exists
        filepath = data["filepath"]
        if not os.path.exists(filepath):
            log.warning(f"Attachment file does not exist: {filepath}")
            # Still return the attachment as the file might be created later
            
        return Attachment(
            url=URL(uri="file://" + filepath),
            mime_type=mimetype,
        )
    except Exception as e:
        log.error(f"Unexpected error interpreting content as attachment: {e}")
        return None

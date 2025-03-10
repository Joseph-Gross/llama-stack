# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.

from typing import AsyncGenerator, List, Optional, Union
import aiohttp

from llama_stack.apis.common.content_types import (
    InterleavedContent,
    InterleavedContentItem,
)
from llama_stack.apis.inference import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    CompletionRequest,
    CompletionResponse,
    EmbeddingsResponse,
    EmbeddingTaskType,
    Inference,
    LogProbConfig,
    Message,
    ResponseFormat,
    ResponseFormatType,
    SamplingParams,
    TextTruncation,
    ToolChoice,
    ToolConfig,
    ToolDefinition,
)
from llama_stack.apis.models import Model
from llama_stack.distribution.request_headers import NeedsRequestProviderData
from llama_stack.providers.utils.inference.model_registry import (
    ModelRegistryHelper,
)
from llama_stack.providers.utils.inference.openai_compat import (
    convert_message_to_openai_dict,
    get_sampling_options,
    process_chat_completion_response,
    process_chat_completion_stream_response,
    process_completion_response,
    process_completion_stream_response,
)
from llama_stack.providers.utils.inference.prompt_adapter import (
    chat_completion_request_to_prompt,
    completion_request_to_prompt,
    content_has_media,
    interleaved_content_as_str,
    request_has_media,
)

from .config import AccentureImplConfig
from .models import MODEL_ENTRIES


class AccentureInferenceAdapter(ModelRegistryHelper, Inference, NeedsRequestProviderData):
    def __init__(self, config: AccentureImplConfig) -> None:
        ModelRegistryHelper.__init__(self, MODEL_ENTRIES)
        self.config = config
        self.session = None

    async def initialize(self) -> None:
        self.session = aiohttp.ClientSession()

    async def shutdown(self) -> None:
        if self.session:
            await self.session.close()
            self.session = None

    def _get_api_key(self) -> str:
        if self.config.api_key is not None:
            return self.config.api_key.get_secret_value()
        else:
            provider_data = self.get_request_provider_data()
            if provider_data is None or not provider_data.accenture_api_key:
                raise ValueError(
                    'Pass Accenture API Key in the header X-LlamaStack-Provider-Data as { "accenture_api_key": <your api key>}'
                )
            return provider_data.accenture_api_key

    async def _get_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._get_api_key()}",
            "Content-Type": "application/json",
        }

    async def completion(
        self,
        model_id: str,
        content: InterleavedContent,
        sampling_params: Optional[SamplingParams] = SamplingParams(),
        response_format: Optional[ResponseFormat] = None,
        stream: Optional[bool] = False,
        logprobs: Optional[LogProbConfig] = None,
    ) -> AsyncGenerator:
        model = await self.model_store.get_model(model_id)
        request = CompletionRequest(
            model=model.provider_resource_id,
            content=content,
            sampling_params=sampling_params,
            response_format=response_format,
            stream=stream,
            logprobs=logprobs,
        )
        if stream:
            return self._stream_completion(request)
        else:
            return await self._nonstream_completion(request)

    async def _nonstream_completion(self, request: CompletionRequest) -> CompletionResponse:
        params = await self._get_params(request)
        headers = await self._get_headers()
        
        async with self.session.post(
            f"{self.config.url}/completions",
            json=params,
            headers=headers,
        ) as response:
            response.raise_for_status()
            data = await response.json()
            
        return process_completion_response(data)

    async def _stream_completion(self, request: CompletionRequest) -> AsyncGenerator:
        params = await self._get_params(request)
        headers = await self._get_headers()
        
        async with self.session.post(
            f"{self.config.url}/completions",
            json=params,
            headers=headers,
            timeout=60,
        ) as response:
            response.raise_for_status()
            
            async for line in response.content:
                if line.strip():
                    chunk = line.decode("utf-8").strip()
                    if chunk.startswith("data: "):
                        chunk = chunk[6:]
                    if chunk and chunk != "[DONE]":
                        yield process_completion_stream_response(chunk)

    async def chat_completion(
        self,
        model_id: str,
        messages: List[Message],
        sampling_params: Optional[SamplingParams] = SamplingParams(),
        tools: Optional[List[ToolDefinition]] = None,
        tool_choice: Optional[ToolChoice] = ToolChoice.auto,
        response_format: Optional[ResponseFormat] = None,
        stream: Optional[bool] = False,
        logprobs: Optional[LogProbConfig] = None,
        tool_config: Optional[ToolConfig] = None,
    ) -> AsyncGenerator:
        model = await self.model_store.get_model(model_id)
        request = ChatCompletionRequest(
            model=model.provider_resource_id,
            messages=messages,
            sampling_params=sampling_params,
            tools=tools or [],
            response_format=response_format,
            stream=stream,
            logprobs=logprobs,
            tool_config=tool_config,
        )

        if stream:
            return self._stream_chat_completion(request)
        else:
            return await self._nonstream_chat_completion(request)

    async def _nonstream_chat_completion(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        params = await self._get_params(request)
        headers = await self._get_headers()
        
        async with self.session.post(
            f"{self.config.url}/chat/completions",
            json=params,
            headers=headers,
        ) as response:
            response.raise_for_status()
            data = await response.json()
            
        return process_chat_completion_response(data, request)

    async def _stream_chat_completion(self, request: ChatCompletionRequest) -> AsyncGenerator:
        params = await self._get_params(request)
        headers = await self._get_headers()
        
        async with self.session.post(
            f"{self.config.url}/chat/completions",
            json=params,
            headers=headers,
            timeout=60,
        ) as response:
            response.raise_for_status()
            
            async for line in response.content:
                if line.strip():
                    chunk = line.decode("utf-8").strip()
                    if chunk.startswith("data: "):
                        chunk = chunk[6:]
                    if chunk and chunk != "[DONE]":
                        async for processed_chunk in process_chat_completion_stream_response(chunk, request):
                            yield processed_chunk

    async def _get_params(self, request: Union[ChatCompletionRequest, CompletionRequest]) -> dict:
        input_dict = {}
        media_present = request_has_media(request)

        if isinstance(request, ChatCompletionRequest):
            if media_present:
                input_dict["messages"] = [
                    await convert_message_to_openai_dict(m, download=True) for m in request.messages
                ]
            else:
                input_dict["messages"] = [
                    await convert_message_to_openai_dict(m, download=False) for m in request.messages
                ]
            
            # Add tools if present
            if request.tools:
                input_dict["tools"] = [
                    {
                        "type": "function",
                        "function": {
                            "name": tool.tool_name,
                            "description": tool.description,
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    param_name: {
                                        "type": param.param_type,
                                        "description": param.description,
                                    }
                                    for param_name, param in (tool.parameters or {}).items()
                                },
                                "required": [
                                    param_name
                                    for param_name, param in (tool.parameters or {}).items()
                                    if param.required
                                ],
                            },
                        },
                    }
                    for tool in request.tools
                ]
                
                # Add tool_choice if specified
                if request.tool_config and request.tool_config.tool_choice:
                    if isinstance(request.tool_config.tool_choice, str):
                        input_dict["tool_choice"] = {
                            "type": "function",
                            "function": {"name": request.tool_config.tool_choice},
                        }
                    else:
                        input_dict["tool_choice"] = request.tool_config.tool_choice.value
        else:
            # Handle completion request
            input_dict["prompt"] = await completion_request_to_prompt(request)

        # Add response format if specified
        if request.response_format:
            if request.response_format.type == ResponseFormatType.json_schema.value:
                input_dict["response_format"] = {"type": "json_object"}
            elif request.response_format.type == ResponseFormatType.grammar.value:
                # Accenture API might not support grammar format
                pass

        return {
            "model": request.model,
            **input_dict,
            "stream": request.stream,
            **get_sampling_options(request.sampling_params),
        }

    async def embeddings(
        self,
        model_id: str,
        contents: List[InterleavedContent],
        text_truncation: Optional[TextTruncation] = TextTruncation.none,
        output_dimension: Optional[int] = None,
        task_type: Optional[EmbeddingTaskType] = None,
    ) -> EmbeddingsResponse:
        model = await self.model_store.get_model(model_id)
        headers = await self._get_headers()
        
        # Convert contents to text
        input_texts = [
            interleaved_content_as_str(content) if not isinstance(content, str) else content
            for content in contents
        ]
        
        params = {
            "model": model.provider_resource_id,
            "input": input_texts,
        }
        
        if output_dimension:
            params["dimensions"] = output_dimension
            
        if task_type:
            params["task_type"] = task_type.value
            
        async with self.session.post(
            f"{self.config.url}/embeddings",
            json=params,
            headers=headers,
        ) as response:
            response.raise_for_status()
            data = await response.json()
            
        # Extract embeddings from response
        embeddings = [item["embedding"] for item in data.get("data", [])]
        return EmbeddingsResponse(embeddings=embeddings)

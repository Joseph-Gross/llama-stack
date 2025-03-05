# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.

import os
import tempfile
from unittest.mock import AsyncMock, MagicMock

import pytest

from llama_stack.apis.agents import (
    AgentConfig,
    Document,
)
from llama_stack.apis.inference import CompletionMessage, UserMessage
from llama_stack.models.llama.datatypes import (
    SamplingParams,
    TopPSamplingStrategy,
)
from llama_models.datatypes import (
    BuiltinTool,
    StopReason,
    ToolCall,
    URL,
)
from llama_stack.providers.inline.agents.meta_reference.agent_instance import (
    ChatAgent,
    load_data_from_urls,
    attachment_message,
    execute_tool_call_maybe,
)

# How to run this test:
#
# pytest llama_stack/providers/tests/integration/test_agent_integration.py \
# -v -s --tb=short --disable-warnings --asyncio-mode=auto


@pytest.fixture
def mock_storage():
    """Create a mock storage for testing."""
    storage = AsyncMock()
    storage.get_session_info = AsyncMock()
    storage.add_vector_db_to_session = AsyncMock()
    storage.get_session_info.return_value = MagicMock(vector_db_id="test_vector_db")
    
    # Add additional methods required by the ChatAgent
    storage.create_session = AsyncMock()
    storage.create_turn = AsyncMock()
    storage.get_turn = AsyncMock()
    storage.update_turn = AsyncMock()
    storage.get_turns = AsyncMock(return_value=[])
    
    return storage


@pytest.fixture
def mock_vector_io_api():
    """Create a mock vector IO API for testing."""
    api = AsyncMock()
    api.register_vector_db = AsyncMock()
    api.unregister_vector_db = AsyncMock()
    api.query_chunks = AsyncMock()
    return api


@pytest.fixture
def mock_tool_runtime_api():
    """Create a mock tool runtime API for testing."""
    api = AsyncMock()
    api.invoke_tool = AsyncMock()
    api.rag_tool = AsyncMock()
    api.rag_tool.insert = AsyncMock()
    return api


@pytest.fixture
def mock_tool_groups_api():
    """Create a mock tool groups API for testing."""
    api = AsyncMock()
    api.list_tools = AsyncMock(return_value=MagicMock(data=[]))
    return api


@pytest.fixture
def mock_inference_api():
    """Create a mock inference API for testing."""
    api = AsyncMock()
    api.generate_completion = AsyncMock(return_value=CompletionMessage(
        content="This is a mock response",
        stop_reason=StopReason.stop,
    ))
    return api


@pytest.fixture
def chat_agent(mock_storage, mock_vector_io_api, mock_tool_runtime_api, mock_tool_groups_api, mock_inference_api):
    """Create a ChatAgent instance for testing."""
    agent_config = AgentConfig(
        model="llama3",
        instructions="You are a helpful assistant.",
        sampling_params=SamplingParams(strategy=TopPSamplingStrategy(temperature=0.7, top_p=0.95)),
    )
    
    agent = ChatAgent(
        agent_id="test_agent",
        agent_config=agent_config,
        tempdir="/tmp",
        persistence_store=mock_storage,
        vector_io_api=mock_vector_io_api,
        tool_runtime_api=mock_tool_runtime_api,
        tool_groups_api=mock_tool_groups_api,
        inference_api=mock_inference_api,
        safety_api=AsyncMock(),  # Use AsyncMock instead of None
    )
    
    return agent


@pytest.mark.asyncio
async def test_agent_document_handling_integration(chat_agent, mock_storage, mock_tool_runtime_api):
    """Test the integration of document handling in the agent."""
    # Create test documents
    documents = [
        Document(content="This is test document 1", mime_type="text/plain"),
        Document(content="This is test document 2", mime_type="text/plain"),
    ]
    
    # Set up the session
    session_id = "test_session"
    
    # Handle the documents
    await chat_agent.handle_documents(session_id, documents)
    
    # Verify that the vector database was ensured
    mock_storage.get_session_info.assert_called_with(session_id)
    
    # Verify that the documents were added to the vector database
    mock_tool_runtime_api.rag_tool.insert.assert_called_once()
    
    # Verify error handling with invalid documents
    invalid_documents = [
        Document(content=None, mime_type="text/plain"),  # Invalid content
    ]
    
    # This should handle the invalid document gracefully
    await chat_agent.handle_documents(session_id, invalid_documents)
    
    # Verify that no insertion was attempted for invalid documents
    assert mock_tool_runtime_api.rag_tool.insert.call_count == 1  # Still only one call from before


@pytest.mark.asyncio
async def test_agent_turn_execution_integration(chat_agent, mock_inference_api, mock_tool_runtime_api):
    """Test the integration of turn execution in the agent."""
    # Set up the session and turn
    session_id = "test_session"
    turn_id = "test_turn"
    
    # Create test messages
    messages = [
        UserMessage(content="Hello, can you help me?"),
    ]
    
    # Configure the inference API to return a completion with a tool call
    tool_call = ToolCall(
        tool_name=BuiltinTool.code_interpreter,
        arguments={"code": "print('Hello, world!')"},
    )
    
    mock_inference_api.generate_completion.return_value = CompletionMessage(
        content="I'll help you with that.",
        stop_reason=StopReason.tool_calls,
        tool_calls=[tool_call],
    )
    
    # Configure the tool runtime API to return a result
    mock_tool_runtime_api.invoke_tool.return_value = MagicMock(
        content="Hello, world!",
        metadata={},
    )
    
    # Execute the turn
    turn_generator = chat_agent._run(
        session_id=session_id,
        turn_id=turn_id,
        messages=messages,
        stream=False,
        documents=None,
        toolgroups=[],
        tool_to_group={"code_interpreter": "builtin"},
        toolgroup_args={},
    )
    
    # Collect the turn events
    turn_events = []
    async for event in turn_generator:
        turn_events.append(event)
    
    # Verify that events were generated
    assert len(turn_events) > 0
    
    # Verify that the inference API was called
    mock_inference_api.generate_completion.assert_called_once()
    
    # Verify that the tool was invoked
    mock_tool_runtime_api.invoke_tool.assert_called_once()


@pytest.mark.asyncio
async def test_agent_error_handling_integration(chat_agent, mock_inference_api, mock_tool_runtime_api):
    """Test the integration of error handling in the agent."""
    # Set up the session and turn
    session_id = "test_session"
    turn_id = "test_turn"
    
    # Create test messages
    messages = [
        UserMessage(content="Hello, can you help me?"),
    ]
    
    # Configure the inference API to raise an exception
    mock_inference_api.generate_completion.side_effect = Exception("Inference error")
    
    # Execute the turn
    turn_generator = chat_agent._run(
        session_id=session_id,
        turn_id=turn_id,
        messages=messages,
        stream=False,
        documents=None,
        toolgroups=[],
        tool_to_group={},
        toolgroup_args={},
    )
    
    # Collect the turn events
    turn_events = []
    async for event in turn_generator:
        turn_events.append(event)
    
    # Verify that error events were generated
    assert len(turn_events) > 0
    
    # Reset the mock
    mock_inference_api.generate_completion.reset_mock()
    mock_inference_api.generate_completion.side_effect = None
    mock_inference_api.generate_completion.return_value = CompletionMessage(
        content="I'll help you with that.",
        stop_reason=StopReason.tool_calls,
        tool_calls=[ToolCall(
            tool_name=BuiltinTool.code_interpreter,
            arguments={"code": "print('Hello, world!')"},
        )],
    )
    
    # Configure the tool runtime API to raise an exception
    mock_tool_runtime_api.invoke_tool.side_effect = Exception("Tool error")
    
    # Execute the turn again
    turn_generator = chat_agent._run(
        session_id=session_id,
        turn_id=turn_id,
        messages=messages,
        stream=False,
        documents=None,
        toolgroups=["builtin"],
        tool_to_group={"code_interpreter": "builtin"},
        toolgroup_args={},
    )
    
    # Collect the turn events
    turn_events = []
    async for event in turn_generator:
        turn_events.append(event)
    
    # Verify that events were generated
    assert len(turn_events) > 0
    
    # Verify that the inference API was called
    mock_inference_api.generate_completion.assert_called_once()
    
    # Verify that the tool was invoked
    mock_tool_runtime_api.invoke_tool.assert_called_once()


@pytest.mark.asyncio
async def test_url_handling_integration():
    """Test the integration of URL handling functions."""
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a test file
        test_file_path = os.path.join(temp_dir, "test_file.txt")
        with open(test_file_path, "w") as f:
            f.write("This is a test file")
        
        # Test loading data from file URL
        file_url = URL(uri=f"file://{test_file_path}")
        file_data = await load_data_from_urls([file_url])
        
        # Verify that the file was loaded
        assert len(file_data) == 1
        assert file_data[0] == "This is a test file"
        
        # Test attachment message with file URL
        attachment_result = await attachment_message(temp_dir, [file_url])
        
        # Verify that the attachment message was created
        assert attachment_result.tool_name == BuiltinTool.code_interpreter
        assert len(attachment_result.content) == 1
        
        # Test error handling with invalid URL
        invalid_url = URL(uri="file:///nonexistent/file.txt")
        invalid_data = await load_data_from_urls([invalid_url])
        
        # Verify that no data was loaded
        assert len(invalid_data) == 0
        
        # Test error handling with invalid URL in attachment message
        invalid_attachment = await attachment_message(temp_dir, [invalid_url])
        
        # Verify that no attachments were created
        assert len(invalid_attachment.content) == 0


@pytest.mark.asyncio
async def test_tool_execution_integration(mock_tool_runtime_api):
    """Test the integration of tool execution."""
    # Create a tool call
    tool_call = ToolCall(
        tool_name=BuiltinTool.code_interpreter,
        arguments={"code": "print('Hello, world!')"},
    )
    
    # Create a tool_to_group mapping
    tool_to_group = {BuiltinTool.code_interpreter: "builtin"}
    
    # Configure the tool runtime API to return a result
    mock_tool_runtime_api.invoke_tool.return_value = MagicMock(
        content="Hello, world!",
        metadata={},
    )
    
    # Execute the tool
    result = await execute_tool_call_maybe(
        tool_runtime_api=mock_tool_runtime_api,
        session_id="test_session",
        tool_call=tool_call,
        toolgroup_args={},
        tool_to_group=tool_to_group,
    )
    
    # Verify that the tool was invoked
    mock_tool_runtime_api.invoke_tool.assert_called_once()
    
    # Verify that the result was returned
    assert result.content == "Hello, world!"
    
    # Test error handling with invalid tool
    invalid_tool_call = ToolCall(
        tool_name="nonexistent_tool",
        arguments={},
    )
    
    # This should raise a ValueError
    with pytest.raises(ValueError):
        await execute_tool_call_maybe(
            tool_runtime_api=mock_tool_runtime_api,
            session_id="test_session",
            tool_call=invalid_tool_call,
            toolgroup_args={},
            tool_to_group=tool_to_group,
        )
    
    # Configure the tool runtime API to raise an exception
    mock_tool_runtime_api.invoke_tool.side_effect = Exception("Tool error")
    
    # Execute the tool again
    result = await execute_tool_call_maybe(
        tool_runtime_api=mock_tool_runtime_api,
        session_id="test_session",
        tool_call=tool_call,
        toolgroup_args={},
        tool_to_group=tool_to_group,
    )
    
    # Verify that an error result was returned
    assert "Error invoking tool" in result.content

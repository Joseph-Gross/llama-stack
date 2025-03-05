# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.

from unittest.mock import MagicMock, AsyncMock, patch

import pytest
import httpx

from llama_stack.apis.agents import (
    AgentConfig,
    Document,
)
from llama_models.datatypes import ToolCall, URL
from llama_stack.models.llama.datatypes import (
    SamplingParams,
    TopPSamplingStrategy,
)
from llama_stack.providers.inline.agents.meta_reference.agent_instance import (
    ChatAgent,
    load_data_from_urls,
    attachment_message,
    execute_tool_call_maybe,
    _interpret_content_as_attachment,
)

# How to run this test:
#
# pytest -v -s llama_stack/providers/tests/agents/test_agent_instance_error_handling.py


@pytest.fixture
def mock_storage():
    storage = AsyncMock()
    storage.get_session_info = AsyncMock()
    storage.add_vector_db_to_session = AsyncMock()
    return storage


@pytest.fixture
def mock_vector_io_api():
    api = AsyncMock()
    api.register_vector_db = AsyncMock()
    api.unregister_vector_db = AsyncMock()
    return api


@pytest.fixture
def mock_tool_runtime_api():
    api = AsyncMock()
    api.invoke_tool = AsyncMock()
    api.rag_tool = AsyncMock()
    api.rag_tool.insert = AsyncMock()
    return api


@pytest.fixture
def mock_tool_groups_api():
    api = AsyncMock()
    api.list_tools = AsyncMock(return_value=MagicMock(data=[]))
    return api


@pytest.fixture
def mock_inference_api():
    api = AsyncMock()
    return api


@pytest.fixture
def chat_agent(mock_storage, mock_vector_io_api, mock_tool_runtime_api, mock_tool_groups_api, mock_inference_api):
    agent_config = AgentConfig(
        model="llama3",
        instructions="You are a helpful assistant.",
        sampling_params=SamplingParams(strategy=TopPSamplingStrategy(temperature=0.7, top_p=0.95)),
    )
    
    agent = ChatAgent(
        agent_id="test_agent",
        agent_config=agent_config,
        tempdir="/tmp/test_agent",  # Use a more specific tempdir
        persistence_store=mock_storage,  # Use persistence_store instead of storage
        vector_io_api=mock_vector_io_api,
        tool_runtime_api=mock_tool_runtime_api,
        tool_groups_api=mock_tool_groups_api,
        inference_api=mock_inference_api,
        safety_api=AsyncMock(),  # Use AsyncMock instead of None
    )
    
    return agent


@pytest.mark.asyncio
async def test_ensure_vector_db_session_not_found(chat_agent, mock_storage):
    """Test that _ensure_vector_db handles session not found errors."""
    # Configure mock to return None (session not found)
    mock_storage.get_session_info.return_value = None
    
    # This should raise a ValueError with a specific message
    with pytest.raises(ValueError, match="Session test_session not found"):
        await chat_agent._ensure_vector_db("test_session")


@pytest.mark.asyncio
async def test_ensure_vector_db_registration_error(chat_agent, mock_storage, mock_vector_io_api):
    """Test that _ensure_vector_db handles vector DB registration errors."""
    # Configure mock to return a session without a vector DB
    session_info = MagicMock()
    session_info.vector_db_id = None
    mock_storage.get_session_info.return_value = session_info
    
    # Configure vector_io_api to raise an exception
    mock_vector_io_api.register_vector_db.side_effect = Exception("Registration error")
    
    # This should raise a RuntimeError with a specific message
    with pytest.raises(RuntimeError, match="Failed to register vector database"):
        await chat_agent._ensure_vector_db("test_session")


@pytest.mark.asyncio
async def test_add_to_session_vector_db_empty_data(chat_agent):
    """Test that add_to_session_vector_db handles empty data gracefully."""
    # Call with empty data
    await chat_agent.add_to_session_vector_db("test_session", [])
    
    # Verify that no further calls were made
    chat_agent.tool_runtime_api.rag_tool.insert.assert_not_called()


@pytest.mark.asyncio
async def test_add_to_session_vector_db_invalid_document(chat_agent, mock_storage):
    """Test that add_to_session_vector_db handles invalid documents gracefully."""
    # Configure mock to return a session with a vector DB
    session_info = MagicMock()
    session_info.vector_db_id = "test_vector_db"
    mock_storage.get_session_info.return_value = session_info
    
    # Create a document that will cause an error during conversion
    invalid_doc = Document(content=None, mime_type="text/plain")
    
    # This should not raise an exception due to our error handling
    await chat_agent.add_to_session_vector_db("test_session", [invalid_doc])
    
    # Verify that no insert was attempted
    chat_agent.tool_runtime_api.rag_tool.insert.assert_not_called()


@pytest.mark.asyncio
async def test_load_data_from_urls_file_not_found():
    """Test that load_data_from_urls handles file not found errors."""
    # Create a URL for a nonexistent file
    url = URL(uri="file:///nonexistent/file.txt")
    
    # This should not raise an exception due to our error handling
    result = await load_data_from_urls([url])
    
    # Verify that the result is an empty list
    assert result == []


@pytest.mark.asyncio
async def test_load_data_from_urls_http_error():
    """Test that load_data_from_urls handles HTTP errors."""
    # Create a URL that will cause an HTTP error
    url = URL(uri="http://example.com/nonexistent")
    
    # Mock httpx.AsyncClient to raise an exception
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.get.side_effect = httpx.HTTPStatusError(
        "404 Not Found", 
        request=MagicMock(), 
        response=MagicMock(status_code=404)
    )
    
    # Patch httpx.AsyncClient to return our mock
    with patch("httpx.AsyncClient", return_value=mock_client):
        # This should not raise an exception due to our error handling
        result = await load_data_from_urls([url])
        
        # Verify that the result is an empty list
        assert result == []


@pytest.mark.asyncio
async def test_attachment_message_invalid_tempdir():
    """Test that attachment_message handles invalid temporary directory."""
    # This should raise a ValueError with a specific message
    with pytest.raises(ValueError, match="Invalid temporary directory"):
        await attachment_message("/nonexistent/dir", [URL(uri="file:///some/file.txt")])


@pytest.mark.asyncio
async def test_attachment_message_empty_urls():
    """Test that attachment_message handles empty URLs gracefully."""
    # Create a temporary directory
    temp_dir = "/tmp"
    
    # Call with empty URLs
    result = await attachment_message(temp_dir, [])
    
    # Verify that the result is a valid message with empty content
    assert result.content == []


@pytest.mark.asyncio
async def test_execute_tool_call_maybe_missing_tool():
    """Test that execute_tool_call_maybe handles missing tools gracefully."""
    # Create a mock tool runtime API
    tool_runtime_api = AsyncMock()
    
    # Create a tool call
    tool_call = ToolCall(tool_name="nonexistent_tool", arguments={})
    
    # Create an empty tool_to_group mapping
    tool_to_group = {}
    
    # This should raise a ValueError with a specific message
    with pytest.raises(ValueError, match="Tool nonexistent_tool not found in any tool group"):
        await execute_tool_call_maybe(
            tool_runtime_api=tool_runtime_api,
            session_id="test_session",
            tool_call=tool_call,
            toolgroup_args={},
            tool_to_group=tool_to_group,
        )


@pytest.mark.asyncio
async def test_execute_tool_call_maybe_tool_error(mock_tool_runtime_api):
    """Test that execute_tool_call_maybe handles tool execution errors gracefully."""
    # Configure mock to raise an exception
    mock_tool_runtime_api.invoke_tool.side_effect = Exception("Tool execution error")
    
    # Create a tool call
    tool_call = ToolCall(tool_name="test_tool", arguments={})
    
    # Create a tool_to_group mapping
    tool_to_group = {"test_tool": "test_group"}
    
    # This should not raise an exception due to our error handling
    result = await execute_tool_call_maybe(
        tool_runtime_api=mock_tool_runtime_api,
        session_id="test_session",
        tool_call=tool_call,
        toolgroup_args={},
        tool_to_group=tool_to_group,
    )
    
    # Verify that the result contains an error message
    assert "Error invoking tool" in result.content


def test_interpret_content_as_attachment_invalid_json():
    """Test that _interpret_content_as_attachment handles invalid JSON gracefully."""
    # Create content with invalid JSON
    content = "```json\n{invalid json}\n```"
    
    # This should not raise an exception due to our error handling
    result = _interpret_content_as_attachment(content)
    
    # Verify that the result is None
    assert result is None


def test_interpret_content_as_attachment_missing_filepath():
    """Test that _interpret_content_as_attachment handles missing filepath gracefully."""
    # Create content with JSON missing the filepath
    content = "```json\n{\"mimetype\": \"text/plain\"}\n```"
    
    # This should not raise an exception due to our error handling
    result = _interpret_content_as_attachment(content)
    
    # Verify that the result is None
    assert result is None


def test_interpret_content_as_attachment_missing_mimetype():
    """Test that _interpret_content_as_attachment handles missing mimetype gracefully."""
    # Create content with JSON missing the mimetype
    content = "```json\n{\"filepath\": \"/path/to/file.txt\"}\n```"
    
    # This should not raise an exception due to our error handling
    result = _interpret_content_as_attachment(content)
    
    # Verify that the result is a valid attachment with a default mimetype
    assert result is not None
    assert result.mime_type == "application/octet-stream"

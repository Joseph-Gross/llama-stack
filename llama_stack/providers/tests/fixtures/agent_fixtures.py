# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.

import json
import os
import tempfile
from typing import Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock

import pytest

from llama_stack.apis.agents import (
    AgentConfig,
    Document,
    Turn,
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


@pytest.fixture(scope="function")
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture(scope="function")
def sample_agent_config():
    """Create a sample agent configuration for testing."""
    return AgentConfig(
        model="llama3",
        instructions="You are a helpful assistant.",
        sampling_params=SamplingParams(strategy=TopPSamplingStrategy(temperature=0.7, top_p=0.95)),
    )


@pytest.fixture(scope="function")
def sample_user_messages():
    """Create sample user messages for testing."""
    return [
        UserMessage(content="Hello, can you help me?"),
        UserMessage(content="I need information about machine learning."),
        UserMessage(content="What is the difference between supervised and unsupervised learning?"),
    ]


@pytest.fixture(scope="function")
def sample_completion_message():
    """Create a sample completion message for testing."""
    return CompletionMessage(
        content="I'd be happy to help you with information about machine learning.",
        stop_reason=StopReason.stop,
    )


@pytest.fixture(scope="function")
def sample_completion_with_tool_call():
    """Create a sample completion message with a tool call for testing."""
    return CompletionMessage(
        content="I'll help you with that.",
        stop_reason=StopReason.tool_calls,
        tool_calls=[
            ToolCall(
                tool_name=BuiltinTool.code_interpreter,
                arguments={"code": "print('Hello, world!')"},
            ),
        ],
    )


@pytest.fixture(scope="function")
def sample_documents():
    """Create sample documents for testing."""
    return [
        Document(content="This is test document 1", mime_type="text/plain"),
        Document(content="This is test document 2", mime_type="text/plain"),
        Document(content="This is test document 3", mime_type="text/plain"),
    ]


@pytest.fixture(scope="function")
def invalid_documents():
    """Create invalid documents for testing error handling."""
    return [
        Document(content=None, mime_type="text/plain"),  # Invalid content
        Document(content="Valid content", mime_type=None),  # Invalid mime_type
        Document(content="", mime_type="text/plain"),  # Empty content
    ]


@pytest.fixture(scope="function")
def sample_urls(temp_dir):
    """Create sample URLs for testing."""
    # Create test files
    urls = []
    for i in range(3):
        file_path = os.path.join(temp_dir, f"test_file_{i}.txt")
        with open(file_path, "w") as f:
            f.write(f"This is test file {i}")
        urls.append(URL(uri=f"file://{file_path}"))
    
    # Add an HTTP URL
    urls.append(URL(uri="http://example.com"))
    
    return urls


@pytest.fixture(scope="function")
def invalid_urls():
    """Create invalid URLs for testing error handling."""
    return [
        URL(uri="file:///nonexistent/file.txt"),  # Nonexistent file
        URL(uri="invalid://example.com"),  # Invalid scheme
        URL(uri=None),  # None URI
    ]


@pytest.fixture(scope="function")
def sample_tool_calls():
    """Create sample tool calls for testing."""
    return [
        ToolCall(
            tool_name=BuiltinTool.code_interpreter,
            arguments={"code": "print('Hello, world!')"},
        ),
        ToolCall(
            tool_name=BuiltinTool.brave_search,
            arguments={"query": "machine learning"},
        ),
    ]


@pytest.fixture(scope="function")
def invalid_tool_calls():
    """Create invalid tool calls for testing error handling."""
    return [
        ToolCall(
            tool_name="nonexistent_tool",
            arguments={},
        ),
        ToolCall(
            tool_name=BuiltinTool.code_interpreter,
            arguments=None,
        ),
    ]


@pytest.fixture(scope="function")
def mock_persistence_store():
    """Create a mock persistence store for testing."""
    store = AsyncMock()
    store.get_session_info = AsyncMock()
    store.add_vector_db_to_session = AsyncMock()
    store.get_session_info.return_value = MagicMock(vector_db_id="test_vector_db")
    
    # Add additional methods required by the ChatAgent
    store.create_session = AsyncMock()
    store.create_turn = AsyncMock()
    store.get_turn = AsyncMock()
    store.update_turn = AsyncMock()
    store.get_turns = AsyncMock(return_value=[])
    
    return store


@pytest.fixture(scope="function")
def mock_vector_io_api():
    """Create a mock vector IO API for testing."""
    api = AsyncMock()
    api.register_vector_db = AsyncMock()
    api.unregister_vector_db = AsyncMock()
    api.query_chunks = AsyncMock()
    return api


@pytest.fixture(scope="function")
def mock_tool_runtime_api():
    """Create a mock tool runtime API for testing."""
    api = AsyncMock()
    api.invoke_tool = AsyncMock()
    api.rag_tool = AsyncMock()
    api.rag_tool.insert = AsyncMock()
    return api


@pytest.fixture(scope="function")
def mock_tool_groups_api():
    """Create a mock tool groups API for testing."""
    api = AsyncMock()
    api.list_tools = AsyncMock(return_value=MagicMock(data=[]))
    return api


@pytest.fixture(scope="function")
def mock_inference_api():
    """Create a mock inference API for testing."""
    api = AsyncMock()
    api.generate_completion = AsyncMock(return_value=CompletionMessage(
        content="This is a mock response",
        stop_reason=StopReason.stop,
    ))
    return api


@pytest.fixture(scope="function")
def mock_safety_api():
    """Create a mock safety API for testing."""
    api = AsyncMock()
    api.check_input = AsyncMock(return_value=MagicMock(violation=None))
    api.check_output = AsyncMock(return_value=MagicMock(violation=None))
    return api


@pytest.fixture(scope="function")
def sample_attachment_content():
    """Create sample attachment content for testing."""
    return f"""```json
{{
  "filepath": "/tmp/test_file.txt",
  "mimetype": "text/plain"
}}
```"""


@pytest.fixture(scope="function")
def invalid_attachment_content():
    """Create invalid attachment content for testing error handling."""
    return [
        """```json
{invalid json}
```""",  # Invalid JSON
        """```json
{"mimetype": "text/plain"}
```""",  # Missing filepath
        """```json
{"filepath": "/nonexistent/file.txt"}
```""",  # Missing mimetype
    ]

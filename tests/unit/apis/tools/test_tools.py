# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from llama_stack.apis.tools.tools import (
    Tool,
    ToolDef,
    ToolGroup,
    ToolHost,
    ToolParameter,
    ToolInvocationResult,
    ListToolGroupsResponse,
    ListToolsResponse,
)
from llama_stack.apis.resource import ResourceType
from llama_stack.apis.common.content_types import InterleavedContent


class TestTools:
    """Unit tests for the Tools API."""

    @pytest.fixture
    def mock_tool_groups(self):
        """Create a mock ToolGroups implementation."""
        mock = MagicMock()
        mock.register_tool_group = AsyncMock()
        mock.get_tool_group = AsyncMock()
        mock.list_tool_groups = AsyncMock()
        mock.list_tools = AsyncMock()
        mock.get_tool = AsyncMock()
        mock.unregister_toolgroup = AsyncMock()
        return mock

    @pytest.fixture
    def mock_tool_runtime(self):
        """Create a mock ToolRuntime implementation."""
        mock = MagicMock()
        mock.list_runtime_tools = AsyncMock()
        mock.invoke_tool = AsyncMock()
        return mock

    @pytest.fixture
    def sample_tool_parameter(self):
        """Sample tool parameter for testing."""
        return ToolParameter(
            name="query",
            parameter_type="string",
            description="The search query",
            required=True,
        )

    @pytest.fixture
    def sample_tool(self, sample_tool_parameter):
        """Sample tool for testing."""
        return Tool(
            identifier="web_search",
            provider_id="brave",
            provider_resource_id="brave_search",
            toolgroup_id="websearch",
            tool_host=ToolHost.distribution,
            description="Search the web using Brave Search",
            parameters=[sample_tool_parameter],
            metadata={"version": "1.0"},
        )

    @pytest.fixture
    def sample_tool_group(self):
        """Sample tool group for testing."""
        return ToolGroup(
            identifier="websearch",
            provider_id="brave",
            provider_resource_id="brave_search",
            args={"api_key": "test_key"},
        )

    @pytest.fixture
    def sample_tool_def(self, sample_tool_parameter):
        """Sample tool definition for testing."""
        return ToolDef(
            name="web_search",
            description="Search the web using Brave Search",
            parameters=[sample_tool_parameter],
            metadata={"version": "1.0"},
        )

    async def test_register_tool_group(self, mock_tool_groups):
        """Test registering a tool group functionality."""
        # Setup
        mock_tool_groups.register_tool_group.return_value = None

        # Execute
        result = await mock_tool_groups.register_tool_group(
            toolgroup_id="websearch",
            provider_id="brave",
            args={"api_key": "test_key"},
        )

        # Verify
        assert result is None
        mock_tool_groups.register_tool_group.assert_called_once()

    async def test_get_tool_group(self, mock_tool_groups, sample_tool_group):
        """Test getting a tool group functionality."""
        # Setup
        mock_tool_groups.get_tool_group.return_value = sample_tool_group

        # Execute
        result = await mock_tool_groups.get_tool_group(toolgroup_id="websearch")

        # Verify
        assert isinstance(result, ToolGroup)
        assert result.identifier == "websearch"
        assert result.provider_id == "brave"
        assert result.provider_resource_id == "brave_search"
        assert result.args == {"api_key": "test_key"}
        mock_tool_groups.get_tool_group.assert_called_once_with(toolgroup_id="websearch")

    async def test_list_tool_groups(self, mock_tool_groups, sample_tool_group):
        """Test listing tool groups functionality."""
        # Setup
        mock_tool_groups.list_tool_groups.return_value = ListToolGroupsResponse(data=[sample_tool_group])

        # Execute
        result = await mock_tool_groups.list_tool_groups()

        # Verify
        assert isinstance(result, ListToolGroupsResponse)
        assert len(result.data) == 1
        assert result.data[0].identifier == "websearch"
        mock_tool_groups.list_tool_groups.assert_called_once()

    async def test_list_tools(self, mock_tool_groups, sample_tool):
        """Test listing tools functionality."""
        # Setup
        mock_tool_groups.list_tools.return_value = ListToolsResponse(data=[sample_tool])

        # Execute
        result = await mock_tool_groups.list_tools(toolgroup_id="websearch")

        # Verify
        assert isinstance(result, ListToolsResponse)
        assert len(result.data) == 1
        assert result.data[0].identifier == "web_search"
        assert result.data[0].toolgroup_id == "websearch"
        mock_tool_groups.list_tools.assert_called_once_with(toolgroup_id="websearch")

    async def test_get_tool(self, mock_tool_groups, sample_tool):
        """Test getting a tool functionality."""
        # Setup
        mock_tool_groups.get_tool.return_value = sample_tool

        # Execute
        result = await mock_tool_groups.get_tool(tool_name="web_search")

        # Verify
        assert isinstance(result, Tool)
        assert result.identifier == "web_search"
        assert result.toolgroup_id == "websearch"
        assert result.tool_host == ToolHost.distribution
        assert result.description == "Search the web using Brave Search"
        assert len(result.parameters) == 1
        assert result.parameters[0].name == "query"
        mock_tool_groups.get_tool.assert_called_once_with(tool_name="web_search")

    async def test_unregister_toolgroup(self, mock_tool_groups):
        """Test unregistering a tool group functionality."""
        # Setup
        mock_tool_groups.unregister_toolgroup.return_value = None

        # Execute
        result = await mock_tool_groups.unregister_toolgroup(toolgroup_id="websearch")

        # Verify
        assert result is None
        mock_tool_groups.unregister_toolgroup.assert_called_once_with(toolgroup_id="websearch")

    async def test_list_runtime_tools(self, mock_tool_runtime, sample_tool_def):
        """Test listing runtime tools functionality."""
        # Setup
        mock_tool_runtime.list_runtime_tools.return_value = [sample_tool_def]

        # Execute
        result = await mock_tool_runtime.list_runtime_tools(tool_group_id="websearch")

        # Verify
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0].name == "web_search"
        assert result[0].description == "Search the web using Brave Search"
        mock_tool_runtime.list_runtime_tools.assert_called_once_with(tool_group_id="websearch", mcp_endpoint=None)

    async def test_invoke_tool(self, mock_tool_runtime):
        """Test invoking a tool functionality."""
        # Setup
        tool_invocation_result = ToolInvocationResult(
            content="Search results for 'llama stack'",
            metadata={"result_count": 10},
        )
        mock_tool_runtime.invoke_tool.return_value = tool_invocation_result

        # Execute
        result = await mock_tool_runtime.invoke_tool(
            tool_name="web_search",
            kwargs={"query": "llama stack"},
        )

        # Verify
        assert isinstance(result, ToolInvocationResult)
        assert result.content == "Search results for 'llama stack'"
        assert result.metadata == {"result_count": 10}
        assert result.error_message is None
        assert result.error_code is None
        mock_tool_runtime.invoke_tool.assert_called_once_with(
            tool_name="web_search",
            kwargs={"query": "llama stack"},
        )

    def test_tool_properties(self, sample_tool):
        """Test Tool class properties."""
        assert sample_tool.type == ResourceType.tool.value
        assert sample_tool.toolgroup_id == "websearch"
        assert sample_tool.tool_host == ToolHost.distribution
        assert sample_tool.description == "Search the web using Brave Search"
        assert len(sample_tool.parameters) == 1
        assert sample_tool.parameters[0].name == "query"

    def test_tool_group_properties(self, sample_tool_group):
        """Test ToolGroup class properties."""
        assert sample_tool_group.type == ResourceType.tool_group.value
        assert sample_tool_group.args == {"api_key": "test_key"}
        assert sample_tool_group.mcp_endpoint is None

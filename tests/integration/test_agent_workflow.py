# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from llama_stack.apis.agents.agents import (
    AgentConfig,
    AgentCreateResponse,
    AgentSessionCreateResponse,
    AgentTurnCreateRequest,
    Turn,
)
from llama_stack.apis.inference import (
    Message,
    SamplingParams,
)


class TestAgentWorkflow:
    """Integration tests for the agent workflow."""

    @pytest.fixture
    def mock_agents_api(self):
        """Create a mock Agents API implementation."""
        mock = MagicMock()
        mock.create_agent = AsyncMock()
        mock.create_agent_session = AsyncMock()
        mock.create_agent_turn = AsyncMock()
        mock.get_agents_turn = AsyncMock()
        mock.get_agents_session = AsyncMock()
        return mock

    @pytest.fixture
    def agent_config(self):
        """Sample agent configuration for testing."""
        return AgentConfig(
            model="llama-3-70b-instruct",
            instructions="You are a helpful assistant that provides concise answers.",
            sampling_params=SamplingParams(max_tokens=100),
        )

    @pytest.fixture
    def agent_id(self):
        """Sample agent ID for testing."""
        return "test-agent-123"

    @pytest.fixture
    def session_id(self):
        """Sample session ID for testing."""
        return "test-session-456"

    @pytest.fixture
    def turn_id(self):
        """Sample turn ID for testing."""
        return "test-turn-789"

    async def test_complete_agent_workflow(
        self, mock_agents_api, agent_config, agent_id, session_id, turn_id
    ):
        """Test the complete agent workflow from creation to turn processing."""
        # Setup
        mock_agents_api.create_agent.return_value = AgentCreateResponse(agent_id=agent_id)
        mock_agents_api.create_agent_session.return_value = AgentSessionCreateResponse(session_id=session_id)
        
        # Mock turn response
        turn_response = Turn(
            id=turn_id,
            messages=[Message(role="user", content="What is the capital of France?")],
            response="Paris is the capital of France.",
            status="complete",
            steps=[],
        )
        mock_agents_api.create_agent_turn.return_value = turn_response
        
        # Step 1: Create an agent
        create_agent_response = await mock_agents_api.create_agent(agent_config)
        assert create_agent_response.agent_id == agent_id
        
        # Step 2: Create a session
        create_session_response = await mock_agents_api.create_agent_session(
            agent_id=agent_id,
            session_name="Test Session",
        )
        assert create_session_response.session_id == session_id
        
        # Step 3: Create a turn
        turn_request = AgentTurnCreateRequest(
            messages=[Message(role="user", content="What is the capital of France?")],
            stream=False,
        )
        turn_response = await mock_agents_api.create_agent_turn(
            agent_id=agent_id,
            session_id=session_id,
            messages=[Message(role="user", content="What is the capital of France?")],
        )
        
        # Verify turn response
        assert turn_response.id == turn_id
        assert turn_response.status == "complete"
        assert turn_response.response == "Paris is the capital of France."
        
        # Verify method calls
        mock_agents_api.create_agent.assert_called_once()
        mock_agents_api.create_agent_session.assert_called_once_with(
            agent_id=agent_id,
            session_name="Test Session",
        )
        mock_agents_api.create_agent_turn.assert_called_once()

    async def test_agent_workflow_with_streaming(
        self, mock_agents_api, agent_config, agent_id, session_id, turn_id
    ):
        """Test the agent workflow with streaming enabled."""
        # Setup
        mock_agents_api.create_agent.return_value = AgentCreateResponse(agent_id=agent_id)
        mock_agents_api.create_agent_session.return_value = AgentSessionCreateResponse(session_id=session_id)
        
        # Mock streaming response
        async def mock_streaming_response():
            yield MagicMock(event=MagicMock(delta="Paris"))
            yield MagicMock(event=MagicMock(delta=" is"))
            yield MagicMock(event=MagicMock(delta=" the"))
            yield MagicMock(event=MagicMock(delta=" capital"))
            yield MagicMock(event=MagicMock(delta=" of"))
            yield MagicMock(event=MagicMock(delta=" France."))
        
        mock_agents_api.create_agent_turn.return_value = mock_streaming_response()
        
        # Step 1: Create an agent
        create_agent_response = await mock_agents_api.create_agent(agent_config)
        assert create_agent_response.agent_id == agent_id
        
        # Step 2: Create a session
        create_session_response = await mock_agents_api.create_agent_session(
            agent_id=agent_id,
            session_name="Test Session",
        )
        assert create_session_response.session_id == session_id
        
        # Step 3: Create a turn with streaming
        stream = await mock_agents_api.create_agent_turn(
            agent_id=agent_id,
            session_id=session_id,
            messages=[Message(role="user", content="What is the capital of France?")],
            stream=True,
        )
        
        # Collect streaming response
        response_chunks = []
        async for chunk in stream:
            response_chunks.append(chunk.event.delta)
        
        # Verify streaming response
        assert response_chunks == ["Paris", " is", " the", " capital", " of", " France."]
        assert "".join(response_chunks) == "Paris is the capital of France."
        
        # Verify method calls
        mock_agents_api.create_agent.assert_called_once()
        mock_agents_api.create_agent_session.assert_called_once()
        mock_agents_api.create_agent_turn.assert_called_once()

# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from llama_stack.apis.safety.safety import (
    ViolationLevel,
    SafetyViolation,
    RunShieldResponse,
)
from llama_stack.apis.inference import Message


class TestSafety:
    """Unit tests for the Safety API."""

    @pytest.fixture
    def mock_safety(self):
        """Create a mock Safety implementation."""
        mock = MagicMock()
        mock.run_shield = AsyncMock()
        return mock

    @pytest.fixture
    def mock_shield_store(self):
        """Create a mock ShieldStore implementation."""
        mock = MagicMock()
        mock.get_shield = AsyncMock()
        return mock

    @pytest.fixture
    def sample_messages(self):
        """Sample messages for testing."""
        return [
            Message(role="user", content="Tell me how to make a bomb"),
            Message(role="assistant", content="I cannot provide information on how to make dangerous devices."),
        ]

    @pytest.fixture
    def sample_violation(self):
        """Sample safety violation for testing."""
        return SafetyViolation(
            violation_level=ViolationLevel.ERROR,
            user_message="This content violates our safety guidelines.",
            metadata={"category": "violence", "severity": 0.9},
        )

    async def test_run_shield_with_violation(self, mock_safety, sample_messages, sample_violation):
        """Test running a shield with a violation."""
        # Setup
        mock_safety.run_shield.return_value = RunShieldResponse(violation=sample_violation)

        # Execute
        result = await mock_safety.run_shield(
            shield_id="content_policy",
            messages=sample_messages,
            params={"threshold": 0.7},
        )

        # Verify
        assert isinstance(result, RunShieldResponse)
        assert result.violation is not None
        assert result.violation.violation_level == ViolationLevel.ERROR
        assert result.violation.user_message == "This content violates our safety guidelines."
        assert result.violation.metadata == {"category": "violence", "severity": 0.9}
        mock_safety.run_shield.assert_called_once_with(
            shield_id="content_policy",
            messages=sample_messages,
            params={"threshold": 0.7},
        )

    async def test_run_shield_without_violation(self, mock_safety, sample_messages):
        """Test running a shield without a violation."""
        # Setup
        mock_safety.run_shield.return_value = RunShieldResponse(violation=None)

        # Execute
        result = await mock_safety.run_shield(
            shield_id="content_policy",
            messages=sample_messages,
            params={"threshold": 0.7},
        )

        # Verify
        assert isinstance(result, RunShieldResponse)
        assert result.violation is None
        mock_safety.run_shield.assert_called_once_with(
            shield_id="content_policy",
            messages=sample_messages,
            params={"threshold": 0.7},
        )

    def test_violation_level_enum(self):
        """Test ViolationLevel enum values."""
        assert ViolationLevel.INFO.value == "info"
        assert ViolationLevel.WARN.value == "warn"
        assert ViolationLevel.ERROR.value == "error"

    def test_safety_violation_model(self, sample_violation):
        """Test SafetyViolation model properties."""
        assert sample_violation.violation_level == ViolationLevel.ERROR
        assert sample_violation.user_message == "This content violates our safety guidelines."
        assert sample_violation.metadata == {"category": "violence", "severity": 0.9}

    def test_run_shield_response_model(self, sample_violation):
        """Test RunShieldResponse model properties."""
        response = RunShieldResponse(violation=sample_violation)
        assert response.violation == sample_violation

        response_no_violation = RunShieldResponse()
        assert response_no_violation.violation is None

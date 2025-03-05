# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from llama_stack.apis.batch_inference.batch_inference import (
    BatchCompletionResponse,
    BatchChatCompletionResponse,
)
from llama_stack.apis.inference import (
    CompletionResponse,
    ChatCompletionResponse,
    InterleavedContent,
    Message,
    SamplingParams,
)


class TestBatchInference:
    """Unit tests for the BatchInference API."""

    @pytest.fixture
    def mock_batch_inference(self):
        """Create a mock BatchInference implementation."""
        mock = MagicMock()
        mock.batch_completion = AsyncMock()
        mock.batch_chat_completion = AsyncMock()
        return mock

    @pytest.fixture
    def sample_content_batch(self):
        """Sample content batch for testing."""
        return [
            "What is the capital of France?",
            "What is the capital of Germany?",
        ]

    @pytest.fixture
    def sample_messages_batch(self):
        """Sample messages batch for testing."""
        return [
            [{"role": "user", "content": "What is the capital of France?"}],
            [{"role": "user", "content": "What is the capital of Germany?"}],
        ]

    @pytest.fixture
    def sample_completion_responses(self):
        """Sample completion responses for testing."""
        return [
            CompletionResponse(content="Paris is the capital of France."),
            CompletionResponse(content="Berlin is the capital of Germany."),
        ]

    @pytest.fixture
    def sample_chat_completion_responses(self):
        """Sample chat completion responses for testing."""
        return [
            ChatCompletionResponse(
                completion_message=Message(role="assistant", content="Paris is the capital of France.")
            ),
            ChatCompletionResponse(
                completion_message=Message(role="assistant", content="Berlin is the capital of Germany.")
            ),
        ]

    async def test_batch_completion(self, mock_batch_inference, sample_content_batch, sample_completion_responses):
        """Test batch completion functionality."""
        # Setup
        mock_batch_inference.batch_completion.return_value = BatchCompletionResponse(
            batch=sample_completion_responses
        )

        # Execute
        result = await mock_batch_inference.batch_completion(
            model="llama-3-70b-instruct",
            content_batch=sample_content_batch,
            sampling_params=SamplingParams(max_tokens=50),
        )

        # Verify
        assert isinstance(result, BatchCompletionResponse)
        assert len(result.batch) == 2
        assert result.batch[0].content == "Paris is the capital of France."
        assert result.batch[1].content == "Berlin is the capital of Germany."
        mock_batch_inference.batch_completion.assert_called_once()

    async def test_batch_chat_completion(
        self, mock_batch_inference, sample_messages_batch, sample_chat_completion_responses
    ):
        """Test batch chat completion functionality."""
        # Setup
        mock_batch_inference.batch_chat_completion.return_value = BatchChatCompletionResponse(
            batch=sample_chat_completion_responses
        )

        # Execute
        result = await mock_batch_inference.batch_chat_completion(
            model="llama-3-70b-instruct",
            messages_batch=sample_messages_batch,
            sampling_params=SamplingParams(max_tokens=50),
        )

        # Verify
        assert isinstance(result, BatchChatCompletionResponse)
        assert len(result.batch) == 2
        assert result.batch[0].completion_message.content == "Paris is the capital of France."
        assert result.batch[1].completion_message.content == "Berlin is the capital of Germany."
        mock_batch_inference.batch_chat_completion.assert_called_once()

    async def test_batch_completion_with_empty_batch(self, mock_batch_inference):
        """Test batch completion with an empty batch."""
        # Setup
        mock_batch_inference.batch_completion.return_value = BatchCompletionResponse(batch=[])

        # Execute
        result = await mock_batch_inference.batch_completion(
            model="llama-3-70b-instruct",
            content_batch=[],
            sampling_params=SamplingParams(max_tokens=50),
        )

        # Verify
        assert isinstance(result, BatchCompletionResponse)
        assert len(result.batch) == 0
        mock_batch_inference.batch_completion.assert_called_once()

    async def test_batch_chat_completion_with_empty_batch(self, mock_batch_inference):
        """Test batch chat completion with an empty batch."""
        # Setup
        mock_batch_inference.batch_chat_completion.return_value = BatchChatCompletionResponse(batch=[])

        # Execute
        result = await mock_batch_inference.batch_chat_completion(
            model="llama-3-70b-instruct",
            messages_batch=[],
            sampling_params=SamplingParams(max_tokens=50),
        )

        # Verify
        assert isinstance(result, BatchChatCompletionResponse)
        assert len(result.batch) == 0
        mock_batch_inference.batch_chat_completion.assert_called_once()

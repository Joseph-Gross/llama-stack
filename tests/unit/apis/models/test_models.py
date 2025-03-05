# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from llama_stack.apis.models.models import (
    Model,
    ModelType,
    ListModelsResponse,
)
from llama_stack.apis.resource import ResourceType


class TestModels:
    """Unit tests for the Models API."""

    @pytest.fixture
    def mock_models(self):
        """Create a mock Models implementation."""
        mock = MagicMock()
        mock.list_models = AsyncMock()
        mock.get_model = AsyncMock()
        mock.register_model = AsyncMock()
        mock.unregister_model = AsyncMock()
        return mock

    @pytest.fixture
    def sample_model(self):
        """Sample model for testing."""
        return Model(
            identifier="llama-3-70b-instruct",
            provider_id="meta",
            provider_resource_id="meta-llama/Llama-3-70b-instruct",
            model_type=ModelType.llm,
            metadata={"family": "llama", "version": "3"},
        )

    @pytest.fixture
    def sample_models(self, sample_model):
        """Sample list of models for testing."""
        return [
            sample_model,
            Model(
                identifier="llama-3-8b-instruct",
                provider_id="meta",
                provider_resource_id="meta-llama/Llama-3-8b-instruct",
                model_type=ModelType.llm,
                metadata={"family": "llama", "version": "3"},
            ),
            Model(
                identifier="text-embedding-3-large",
                provider_id="meta",
                provider_resource_id="text-embedding-3-large",
                model_type=ModelType.embedding,
                metadata={"family": "text-embedding", "version": "3"},
            ),
        ]

    async def test_list_models(self, mock_models, sample_models):
        """Test listing models functionality."""
        # Setup
        mock_models.list_models.return_value = ListModelsResponse(data=sample_models)

        # Execute
        result = await mock_models.list_models()

        # Verify
        assert isinstance(result, ListModelsResponse)
        assert len(result.data) == 3
        assert result.data[0].identifier == "llama-3-70b-instruct"
        assert result.data[1].identifier == "llama-3-8b-instruct"
        assert result.data[2].identifier == "text-embedding-3-large"
        mock_models.list_models.assert_called_once()

    async def test_get_model(self, mock_models, sample_model):
        """Test getting a specific model functionality."""
        # Setup
        mock_models.get_model.return_value = sample_model

        # Execute
        result = await mock_models.get_model(model_id="llama-3-70b-instruct")

        # Verify
        assert isinstance(result, Model)
        assert result.identifier == "llama-3-70b-instruct"
        assert result.provider_id == "meta"
        assert result.provider_resource_id == "meta-llama/Llama-3-70b-instruct"
        assert result.model_type == ModelType.llm
        assert result.metadata == {"family": "llama", "version": "3"}
        mock_models.get_model.assert_called_once_with(model_id="llama-3-70b-instruct")

    async def test_get_model_not_found(self, mock_models):
        """Test getting a non-existent model."""
        # Setup
        mock_models.get_model.return_value = None

        # Execute
        result = await mock_models.get_model(model_id="non-existent-model")

        # Verify
        assert result is None
        mock_models.get_model.assert_called_once_with(model_id="non-existent-model")

    async def test_register_model(self, mock_models, sample_model):
        """Test registering a model functionality."""
        # Setup
        mock_models.register_model.return_value = sample_model

        # Execute
        result = await mock_models.register_model(
            model_id="llama-3-70b-instruct",
            provider_id="meta",
            provider_model_id="meta-llama/Llama-3-70b-instruct",
            metadata={"family": "llama", "version": "3"},
            model_type=ModelType.llm,
        )

        # Verify
        assert isinstance(result, Model)
        assert result.identifier == "llama-3-70b-instruct"
        assert result.provider_id == "meta"
        assert result.provider_resource_id == "meta-llama/Llama-3-70b-instruct"
        assert result.model_type == ModelType.llm
        assert result.metadata == {"family": "llama", "version": "3"}
        mock_models.register_model.assert_called_once()

    async def test_unregister_model(self, mock_models):
        """Test unregistering a model functionality."""
        # Setup
        mock_models.unregister_model.return_value = None

        # Execute
        result = await mock_models.unregister_model(model_id="llama-3-70b-instruct")

        # Verify
        assert result is None
        mock_models.unregister_model.assert_called_once_with(model_id="llama-3-70b-instruct")

    def test_model_properties(self, sample_model):
        """Test Model class properties."""
        assert sample_model.model_id == "llama-3-70b-instruct"
        assert sample_model.provider_model_id == "meta-llama/Llama-3-70b-instruct"
        assert sample_model.type == ResourceType.model.value

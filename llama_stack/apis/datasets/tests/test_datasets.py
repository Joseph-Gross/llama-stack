# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.

"""
Unit tests for the Dataset API module.
"""

import pytest
from typing import Dict, List, Optional, Any
from unittest.mock import AsyncMock, MagicMock

from llama_stack.apis.datasets.datasets import (
    CommonDatasetFields,
    Dataset,
    DatasetInput,
    ListDatasetsResponse,
    Datasets,
)
from llama_stack.apis.common.content_types import URL
from llama_stack.apis.resource import ResourceType


@pytest.fixture
def dataset_schema() -> Dict[str, Any]:
    """Fixture for a sample dataset schema."""
    return {
        "text": {"type": "string", "description": "The text content"},
        "label": {"type": "string", "description": "The label for the text"},
    }


@pytest.fixture
def dataset_url() -> URL:
    """Fixture for a sample dataset URL."""
    return URL("https://example.com/datasets/sample")


@pytest.fixture
def dataset_metadata() -> Dict[str, Any]:
    """Fixture for sample dataset metadata."""
    return {
        "description": "A sample dataset for testing",
        "version": "1.0.0",
        "license": "MIT",
    }


@pytest.fixture
def dataset_input(dataset_schema, dataset_url, dataset_metadata) -> DatasetInput:
    """Fixture for a sample DatasetInput instance."""
    return DatasetInput(
        dataset_id="test-dataset",
        dataset_schema=dataset_schema,
        url=dataset_url,
        provider_id="test-provider",
        provider_dataset_id="provider-test-dataset",
        metadata=dataset_metadata,
    )


@pytest.fixture
def dataset(dataset_schema, dataset_url, dataset_metadata) -> Dataset:
    """Fixture for a sample Dataset instance."""
    return Dataset(
        identifier="test-dataset",
        provider_id="test-provider",
        provider_resource_id="provider-test-dataset",
        dataset_schema=dataset_schema,
        url=dataset_url,
        metadata=dataset_metadata,
    )


@pytest.fixture
def mock_datasets_implementation(dataset) -> Datasets:
    """Fixture for a mock implementation of the Datasets protocol."""
    mock = MagicMock(spec=Datasets)
    
    # Set up async methods as AsyncMock
    mock.register_dataset = AsyncMock()
    mock.get_dataset = AsyncMock(return_value=dataset)
    mock.list_datasets = AsyncMock(return_value=ListDatasetsResponse(data=[dataset]))
    mock.unregister_dataset = AsyncMock()
    
    return mock


class TestDatasetModels:
    """Tests for the Dataset API data models."""

    def test_dataset_input_creation(self, dataset_input):
        """Test creating a DatasetInput instance."""
        assert dataset_input.dataset_id == "test-dataset"
        assert dataset_input.provider_id == "test-provider"
        assert dataset_input.provider_dataset_id == "provider-test-dataset"
        assert dataset_input.url.url == "https://example.com/datasets/sample"
        assert "description" in dataset_input.metadata
        assert dataset_input.metadata["version"] == "1.0.0"

    def test_dataset_creation(self, dataset):
        """Test creating a Dataset instance."""
        assert dataset.identifier == "test-dataset"
        assert dataset.provider_id == "test-provider"
        assert dataset.provider_resource_id == "provider-test-dataset"
        assert dataset.type == ResourceType.dataset
        assert dataset.url.url == "https://example.com/datasets/sample"
        assert "description" in dataset.metadata
        assert dataset.metadata["version"] == "1.0.0"

    def test_dataset_properties(self, dataset):
        """Test Dataset property methods."""
        assert dataset.dataset_id == "test-dataset"
        assert dataset.provider_dataset_id == "provider-test-dataset"


class TestDatasetsProtocol:
    """Tests for the Datasets protocol implementation."""

    @pytest.mark.asyncio
    async def test_register_dataset(self, mock_datasets_implementation, dataset_input):
        """Test registering a dataset."""
        await mock_datasets_implementation.register_dataset(
            dataset_id=dataset_input.dataset_id,
            dataset_schema=dataset_input.dataset_schema,
            url=dataset_input.url,
            provider_dataset_id=dataset_input.provider_dataset_id,
            provider_id=dataset_input.provider_id,
            metadata=dataset_input.metadata,
        )
        
        mock_datasets_implementation.register_dataset.assert_called_once_with(
            dataset_id=dataset_input.dataset_id,
            dataset_schema=dataset_input.dataset_schema,
            url=dataset_input.url,
            provider_dataset_id=dataset_input.provider_dataset_id,
            provider_id=dataset_input.provider_id,
            metadata=dataset_input.metadata,
        )

    @pytest.mark.asyncio
    async def test_get_dataset(self, mock_datasets_implementation, dataset):
        """Test retrieving a dataset by ID."""
        result = await mock_datasets_implementation.get_dataset(dataset_id=dataset.dataset_id)
        
        mock_datasets_implementation.get_dataset.assert_called_once_with(
            dataset_id=dataset.dataset_id
        )
        assert result == dataset

    @pytest.mark.asyncio
    async def test_list_datasets(self, mock_datasets_implementation, dataset):
        """Test listing all datasets."""
        result = await mock_datasets_implementation.list_datasets()
        
        mock_datasets_implementation.list_datasets.assert_called_once()
        assert isinstance(result, ListDatasetsResponse)
        assert len(result.data) == 1
        assert result.data[0] == dataset

    @pytest.mark.asyncio
    async def test_unregister_dataset(self, mock_datasets_implementation, dataset):
        """Test unregistering a dataset."""
        await mock_datasets_implementation.unregister_dataset(dataset_id=dataset.dataset_id)
        
        mock_datasets_implementation.unregister_dataset.assert_called_once_with(
            dataset_id=dataset.dataset_id
        )

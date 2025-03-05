# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.

import os
import tempfile
from typing import Dict, List, Optional

import numpy as np
import pytest

from llama_stack.apis.vector_dbs import VectorDB
from llama_stack.apis.vector_io import Chunk, QueryChunksResponse


# Constants for testing
SQLITE_VEC_PROVIDER = "sqlite_vec"
EMBEDDING_DIMENSION = 384
EMBEDDING_MODEL = "all-MiniLM-L6-v2"


@pytest.fixture(scope="function")
def temp_db_path():
    """Create a temporary database file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp_file:
        temp_path = temp_file.name
    
    yield temp_path
    
    # Clean up the temporary file after tests
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture(scope="function")
def sample_vector_db():
    """Create a sample vector database configuration for testing."""
    return VectorDB(
        identifier="test_vector_db",
        embedding_model=EMBEDDING_MODEL,
        embedding_dimension=EMBEDDING_DIMENSION,
        metadata={"test": True},
        provider_id=SQLITE_VEC_PROVIDER,
    )


@pytest.fixture(scope="function")
def sample_chunks():
    """Generate sample chunks for testing."""
    return [
        Chunk(content=f"This is test chunk {i}", metadata={"document_id": f"doc-{i//3}", "chunk_index": i})
        for i in range(10)
    ]


@pytest.fixture(scope="function")
def sample_embeddings(sample_chunks):
    """Generate sample embeddings for testing."""
    from llama_stack.utils.random_utils import get_numpy_random_generator
    
    # Create a random generator with a fixed seed for reproducibility
    rng = get_numpy_random_generator(42)
    
    return np.array([rng.random(EMBEDDING_DIMENSION).astype(np.float32) for _ in sample_chunks])


@pytest.fixture(scope="function")
def sample_query_embedding():
    """Generate a sample query embedding for testing."""
    from llama_stack.utils.random_utils import get_numpy_random_generator
    
    # Create a random generator with a fixed seed for reproducibility
    rng = get_numpy_random_generator(42)
    
    return rng.random(EMBEDDING_DIMENSION).astype(np.float32)


@pytest.fixture(scope="function")
def sample_query_response():
    """Generate a sample query response for testing."""
    chunks = [
        Chunk(content=f"This is result chunk {i}", metadata={"document_id": f"doc-{i}", "score": 0.9 - i*0.1})
        for i in range(3)
    ]
    return QueryChunksResponse(chunks=chunks, metadata={"query_time_ms": 10})


@pytest.fixture(scope="function")
def invalid_chunks():
    """Generate invalid chunks for testing error handling."""
    return [
        Chunk(content=None, metadata={"document_id": "invalid-1"}),  # Invalid content
        Chunk(content="Valid content", metadata=None),  # Invalid metadata
        Chunk(content="", metadata={"document_id": "invalid-3"}),  # Empty content
    ]


@pytest.fixture(scope="function")
def mixed_type_embedding():
    """Generate an embedding with mixed types for testing error handling."""
    mixed_embedding = [1, 2.5, "3", 4.0] + [0.0] * (EMBEDDING_DIMENSION - 4)
    return mixed_embedding


@pytest.fixture(scope="function")
def embedding_with_none():
    """Generate an embedding with None values for testing error handling."""
    embedding_with_none = [1.0, None, 3.0, None] + [0.5] * (EMBEDDING_DIMENSION - 4)
    return embedding_with_none


@pytest.fixture(scope="function")
def wrong_dimension_embeddings(sample_chunks):
    """Generate embeddings with wrong dimensions for testing error handling."""
    np.random.seed(42)  # For reproducibility
    return np.array([np.random.rand(EMBEDDING_DIMENSION - 1).astype(np.float32) for _ in sample_chunks])

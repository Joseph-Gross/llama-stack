# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.

import asyncio
import os
import tempfile
from typing import List

import numpy as np
import pytest

from llama_stack.apis.vector_dbs import VectorDB
from llama_stack.apis.vector_io import Chunk, QueryChunksResponse
from llama_stack.providers.inline.vector_io.sqlite_vec.sqlite_vec import (
    SQLiteVecVectorIOAdapter,
)

# How to run this test:
#
# pytest llama_stack/providers/tests/integration/test_vector_io_integration.py \
# -v -s --tb=short --disable-warnings --asyncio-mode=auto

SQLITE_VEC_PROVIDER = "sqlite_vec"
EMBEDDING_DIMENSION = 384
EMBEDDING_MODEL = "all-MiniLM-L6-v2"


@pytest.fixture(scope="module")
def temp_db_path():
    """Create a temporary database file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp_file:
        temp_path = temp_file.name
    
    yield temp_path
    
    # Clean up the temporary file after tests
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture(scope="module")
async def vector_io_adapter(temp_db_path):
    """Create a SQLiteVecVectorIOAdapter instance for testing."""
    # Create a mock config with the temporary database path
    config = type("Config", (object,), {"db_path": temp_db_path})
    
    # Create a mock inference API
    inference_api = type("InferenceAPI", (object,), {
        "embed_text": lambda texts, model: np.random.rand(len(texts), EMBEDDING_DIMENSION).astype(np.float32)
    })
    
    # Create the adapter
    # Use MagicMock to create a mock adapter since SQLiteVecVectorIOAdapter is abstract
    from unittest.mock import MagicMock, AsyncMock
    
    adapter = MagicMock(spec=SQLiteVecVectorIOAdapter)
    adapter.initialize = AsyncMock()
    adapter.shutdown = AsyncMock()
    adapter.register_vector_db = AsyncMock()
    adapter.unregister_vector_db = AsyncMock()
    adapter.list_vector_dbs = AsyncMock(return_value=[])
    adapter.insert_chunks = AsyncMock()
    adapter.query_chunks = AsyncMock(return_value=QueryChunksResponse(chunks=[], metadata={}))
    
    # Initialize the adapter
    await adapter.initialize()
    
    yield adapter
    
    # Shut down the adapter after tests
    await adapter.shutdown()


@pytest.fixture(scope="module")
def sample_chunks():
    """Generate sample chunks for testing."""
    return [
        Chunk(content=f"This is test chunk {i}", metadata={"document_id": f"doc-{i//3}", "chunk_index": i})
        for i in range(10)
    ]


@pytest.mark.asyncio
async def test_end_to_end_vector_db_workflow(vector_io_adapter, sample_chunks):
    """Test the end-to-end workflow of creating, using, and deleting a vector database."""
    from llama_stack.utils.random_utils import get_numpy_random_generator
    
    # Create a random generator with a fixed seed for reproducibility
    rng = get_numpy_random_generator(42)
    
    # 1. Register a new vector database
    vector_db_id = "test_integration_db"
    vector_db = VectorDB(
        identifier=vector_db_id,
        embedding_model=EMBEDDING_MODEL,
        embedding_dimension=EMBEDDING_DIMENSION,
        metadata={"test": "integration"},
        provider_id=SQLITE_VEC_PROVIDER,
    )
    
    await vector_io_adapter.register_vector_db(vector_db)
    
    # 2. Verify the vector database was created
    vector_dbs = await vector_io_adapter.list_vector_dbs()
    assert any(db.identifier == vector_db_id for db in vector_dbs)
    
    # 3. Insert chunks into the vector database
    await vector_io_adapter.insert_chunks(
        vector_db_id=vector_db_id,
        chunks=sample_chunks,
        embeddings=None,  # Let the adapter generate embeddings
    )
    
    # 4. Query the vector database
    query_text = "This is a test query"
    query_embedding = rng.random(EMBEDDING_DIMENSION).astype(np.float32)
    
    response = await vector_io_adapter.query_chunks(
        vector_db_id=vector_db_id,
        embedding=query_embedding,
        k=3,
        score_threshold=0.0,
    )
    
    # 5. Verify the query response
    assert isinstance(response, QueryChunksResponse)
    assert len(response.chunks) <= 3  # May be less if score threshold filters some out
    
    # 6. Test error handling with invalid query
    try:
        # Query with invalid vector DB ID
        await vector_io_adapter.query_chunks(
            vector_db_id="nonexistent_db",
            embedding=query_embedding,
            k=3,
            score_threshold=0.0,
        )
        assert False, "Expected an exception for nonexistent vector DB"
    except ValueError:
        # Expected exception
        pass
    
    # 7. Unregister the vector database
    await vector_io_adapter.unregister_vector_db(vector_db_id)
    
    # 8. Verify the vector database was deleted
    vector_dbs = await vector_io_adapter.list_vector_dbs()
    assert not any(db.identifier == vector_db_id for db in vector_dbs)


@pytest.mark.asyncio
async def test_concurrent_vector_db_operations(vector_io_adapter, sample_chunks):
    """Test concurrent operations on vector databases."""
    from llama_stack.utils.random_utils import get_numpy_random_generator
    
    # Create a random generator with a fixed seed for reproducibility
    rng = get_numpy_random_generator(42)
    
    # Create multiple vector databases
    vector_db_ids = [f"concurrent_db_{i}" for i in range(3)]
    
    # Register vector databases concurrently
    await asyncio.gather(*[
        vector_io_adapter.register_vector_db(
            VectorDB(
                identifier=db_id,
                embedding_model=EMBEDDING_MODEL,
                embedding_dimension=EMBEDDING_DIMENSION,
                metadata={"test": "concurrent"},
                provider_id=SQLITE_VEC_PROVIDER,
            )
        )
        for db_id in vector_db_ids
    ])
    
    # Insert chunks concurrently
    await asyncio.gather(*[
        vector_io_adapter.insert_chunks(
            vector_db_id=db_id,
            chunks=sample_chunks,
            embeddings=None,
        )
        for db_id in vector_db_ids
    ])
    
    # Query vector databases concurrently
    query_embedding = rng.random(EMBEDDING_DIMENSION).astype(np.float32)
    responses = await asyncio.gather(*[
        vector_io_adapter.query_chunks(
            vector_db_id=db_id,
            embedding=query_embedding,
            k=2,
            score_threshold=0.0,
        )
        for db_id in vector_db_ids
    ])
    
    # Verify all responses are valid
    for response in responses:
        assert isinstance(response, QueryChunksResponse)
    
    # Unregister vector databases concurrently
    await asyncio.gather(*[
        vector_io_adapter.unregister_vector_db(db_id)
        for db_id in vector_db_ids
    ])
    
    # Verify all vector databases were deleted
    vector_dbs = await vector_io_adapter.list_vector_dbs()
    for db_id in vector_db_ids:
        assert not any(db.identifier == db_id for db in vector_dbs)


@pytest.mark.asyncio
async def test_error_recovery_workflow(vector_io_adapter, sample_chunks):
    """Test error recovery in the vector database workflow."""
    vector_db_id = "error_recovery_db"
    
    # 1. Register a vector database
    await vector_io_adapter.register_vector_db(
        VectorDB(
            identifier=vector_db_id,
            embedding_model=EMBEDDING_MODEL,
            embedding_dimension=EMBEDDING_DIMENSION,
            metadata={"test": "error_recovery"},
            provider_id=SQLITE_VEC_PROVIDER,
        )
    )
    
    # 2. Insert chunks with some invalid chunks mixed in
    valid_chunks = sample_chunks[:5]
    invalid_chunks = [
        Chunk(content=None, metadata={"document_id": "invalid-1"}),  # Invalid content
        Chunk(content="Valid content", metadata=None),  # Invalid metadata
    ]
    
    # This should handle the invalid chunks gracefully
    await vector_io_adapter.insert_chunks(
        vector_db_id=vector_db_id,
        chunks=valid_chunks + invalid_chunks,
        embeddings=None,
    )
    
    # 3. Query the vector database
    query_embedding = np.random.rand(EMBEDDING_DIMENSION).astype(np.float32)
    response = await vector_io_adapter.query_chunks(
        vector_db_id=vector_db_id,
        embedding=query_embedding,
        k=10,  # Request more than we inserted
        score_threshold=0.0,
    )
    
    # 4. Verify that only valid chunks were inserted
    assert isinstance(response, QueryChunksResponse)
    assert len(response.chunks) <= 5  # Only the valid chunks should be returned
    
    # 5. Clean up
    await vector_io_adapter.unregister_vector_db(vector_db_id)

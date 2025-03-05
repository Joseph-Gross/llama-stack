# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.

import asyncio
import sqlite3
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
import sqlite_vec

from llama_stack.apis.vector_dbs import VectorDB
from llama_stack.apis.vector_io import Chunk, QueryChunksResponse
from llama_stack.providers.inline.vector_io.sqlite_vec.sqlite_vec import (
    SQLiteVecIndex,
    SQLiteVecVectorIOAdapter,
    generate_chunk_id,
)

# How to run this test:
#
# pytest llama_stack/providers/tests/vector_io/test_sqlite_vec_error_handling.py \
# -v -s --tb=short --disable-warnings --asyncio-mode=auto

SQLITE_VEC_PROVIDER = "sqlite_vec"
EMBEDDING_DIMENSION = 384
EMBEDDING_MODEL = "all-MiniLM-L6-v2"


@pytest.fixture(scope="session")
def loop():
    return asyncio.new_event_loop()


@pytest.fixture(scope="session", autouse=True)
def sqlite_connection(loop):
    conn = sqlite3.connect(":memory:")
    try:
        conn.enable_load_extension(True)
        sqlite_vec.load(conn)
        yield conn
    finally:
        conn.close()


@pytest.fixture(scope="session", autouse=True)
async def sqlite_vec_index(sqlite_connection):
    return await SQLiteVecIndex.create(dimension=EMBEDDING_DIMENSION, connection=sqlite_connection, bank_id="test_bank")


@pytest.fixture(scope="session")
def sample_chunks():
    """Generates sample chunks for testing."""
    n, k = 5, 2
    sample = [
        Chunk(content=f"Sentence {i} from document {j}", metadata={"document_id": f"document-{j}"})
        for j in range(k)
        for i in range(n)
    ]
    return sample


@pytest.fixture(scope="session")
def sample_embeddings(sample_chunks):
    np.random.seed(42)
    return np.array([np.random.rand(EMBEDDING_DIMENSION).astype(np.float32) for _ in sample_chunks])


@pytest.fixture(scope="session")
async def sqlite_vec_adapter(sqlite_connection):
    config = type("Config", (object,), {"db_path": ":memory:"})  # Mock config with in-memory database
    adapter = SQLiteVecVectorIOAdapter(config=config, inference_api=None)
    await adapter.initialize()
    yield adapter
    await adapter.shutdown()


@pytest.mark.asyncio
async def test_query_with_invalid_embedding_types(sqlite_vec_index):
    """Test that the query method handles invalid embedding types gracefully."""
    from llama_stack.utils.random_utils import set_random_seed
    
    # Set a fixed seed for reproducibility
    set_random_seed(42)
    
    # Test with mixed types (int, float, string)
    mixed_embedding = [1, 2.5, "3", 4.0] + [0.0] * (EMBEDDING_DIMENSION - 4)
    
    # This should not raise an exception due to our error handling
    response = await sqlite_vec_index.query(mixed_embedding, k=2, score_threshold=0.0)
    
    # Verify the response is valid
    assert isinstance(response, QueryChunksResponse)


@pytest.mark.asyncio
async def test_query_with_none_values(sqlite_vec_index):
    """Test that the query method handles None values in embeddings."""
    # Create an embedding with None values
    embedding_with_none = [1.0, None, 3.0, None] + [0.5] * (EMBEDDING_DIMENSION - 4)
    
    # This should not raise an exception due to our error handling
    response = await sqlite_vec_index.query(embedding_with_none, k=2, score_threshold=0.0)
    
    # Verify the response is valid
    assert isinstance(response, QueryChunksResponse)


@pytest.mark.asyncio
async def test_add_chunks_with_invalid_embeddings(sqlite_vec_index, sample_chunks):
    """Test that add_chunks handles invalid embeddings gracefully."""
    # Create invalid embeddings (wrong dimension)
    invalid_embeddings = np.random.rand(len(sample_chunks), EMBEDDING_DIMENSION - 1).astype(np.float32)
    
    # This should raise a specific error due to dimension mismatch
    with pytest.raises(ValueError, match="Embedding dimension mismatch"):
        await sqlite_vec_index.add_chunks(sample_chunks, invalid_embeddings)


@pytest.mark.asyncio
async def test_register_vector_db_with_duplicate_id(sqlite_vec_adapter):
    """Test that register_vector_db handles duplicate IDs gracefully."""
    vector_db = VectorDB(
        identifier="duplicate_db",
        embedding_model=EMBEDDING_MODEL,
        embedding_dimension=EMBEDDING_DIMENSION,
        metadata={},
        provider_id=SQLITE_VEC_PROVIDER,
    )
    
    # Register the first time should succeed
    await sqlite_vec_adapter.register_vector_db(vector_db)
    
    # Register with the same ID should raise a specific error
    with pytest.raises(ValueError, match="Vector DB with ID duplicate_db already exists"):
        await sqlite_vec_adapter.register_vector_db(vector_db)


@pytest.mark.asyncio
async def test_unregister_nonexistent_vector_db(sqlite_vec_adapter):
    """Test that unregister_vector_db handles nonexistent IDs gracefully."""
    # This should not raise an exception due to our error handling
    await sqlite_vec_adapter.unregister_vector_db("nonexistent_db")
    
    # Verify that the operation completed without errors
    vector_dbs = await sqlite_vec_adapter.list_vector_dbs()
    assert not any(db.identifier == "nonexistent_db" for db in vector_dbs)


@pytest.mark.asyncio
async def test_query_chunks_with_invalid_vector_db_id(sqlite_vec_adapter, sample_embeddings):
    """Test that query_chunks handles invalid vector DB IDs gracefully."""
    # This should raise a specific error
    with pytest.raises(ValueError, match="Vector DB with ID nonexistent_db not found"):
        await sqlite_vec_adapter.query_chunks(
            vector_db_id="nonexistent_db",
            embedding=sample_embeddings[0],
            k=2,
            score_threshold=0.0,
        )


@pytest.mark.asyncio
async def test_insert_chunks_with_invalid_vector_db_id(sqlite_vec_adapter, sample_chunks, sample_embeddings):
    """Test that insert_chunks handles invalid vector DB IDs gracefully."""
    # This should raise a specific error
    with pytest.raises(ValueError, match="Vector DB with ID nonexistent_db not found"):
        await sqlite_vec_adapter.insert_chunks(
            vector_db_id="nonexistent_db",
            chunks=sample_chunks,
            embeddings=sample_embeddings,
        )


@pytest.mark.asyncio
async def test_sqlite_connection_error_handling():
    """Test that SQLite connection errors are handled gracefully."""
    # Create a mock connection that raises an exception when used
    mock_connection = MagicMock()
    mock_connection.cursor.side_effect = sqlite3.Error("Mock SQLite error")
    
    # Create an index with the mock connection
    index = SQLiteVecIndex(dimension=EMBEDDING_DIMENSION, connection=mock_connection, bank_id="test_bank")
    
    # Test that query handles the connection error gracefully
    with pytest.raises(RuntimeError, match="SQLite error"):
        await index.query(np.random.rand(EMBEDDING_DIMENSION).astype(np.float32), k=2)


@pytest.mark.asyncio
async def test_initialize_with_connection_error():
    """Test that initialize handles connection errors gracefully."""
    config = type("Config", (object,), {"db_path": "/nonexistent/path.db"})
    adapter = SQLiteVecVectorIOAdapter(config=config, inference_api=None)
    
    # Patch sqlite3.connect to raise an exception
    with patch("sqlite3.connect", side_effect=sqlite3.Error("Mock connection error")):
        # This should raise a RuntimeError with a specific message
        with pytest.raises(RuntimeError, match="Failed to initialize SQLite database"):
            await adapter.initialize()

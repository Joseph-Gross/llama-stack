# Vector Database Operations in Llama Stack

This document provides a detailed explanation of vector database operations in Llama Stack, focusing on the SQLiteVec implementation. Understanding these operations is essential for researchers working with vector embeddings and similarity search.

## Overview

Vector databases store and index embeddings (numerical representations of text or other data) to enable efficient similarity search. In Llama Stack, the primary vector database implementation is `SQLiteVecVectorIOAdapter`, which uses SQLite with the sqlite-vec extension.

## Key Components

### 1. Vector Database Registration

Before using a vector database, it must be registered with the system:

```python
vector_db = VectorDB(
    identifier="research_db",
    embedding_model="all-MiniLM-L6-v2",
    embedding_dimension=384,
    metadata={"purpose": "research"},
    provider_id="sqlite_vec",
)

await vector_io_adapter.register_vector_db(vector_db)
```

This process:
1. Creates a unique identifier for the database
2. Specifies the embedding model and dimension
3. Stores metadata about the database
4. Initializes the necessary database tables

### 2. Database Structure

The SQLiteVec implementation uses two tables for each vector database:

1. **Metadata Table** (`chunks_{bank_id}`):
   - Stores chunk content and metadata as JSON
   - Primary key is a unique chunk ID

2. **Vector Table** (`vec_chunks_{bank_id}`):
   - Virtual table using the sqlite-vec extension
   - Stores embeddings as binary data
   - Linked to metadata via chunk ID

### 3. Chunk Insertion

Inserting chunks into a vector database involves:

```python
await vector_io_adapter.insert_chunks(
    vector_db_id="research_db",
    chunks=document_chunks,
    ttl_seconds=None,  # Optional time-to-live
)
```

This process:
1. Converts chunks to embeddings using the specified embedding model
2. Generates unique IDs for each chunk
3. Serializes embeddings to binary format
4. Stores chunk metadata and embeddings in their respective tables
5. Uses batch processing for efficiency (default batch size: 500)

### 4. Vector Querying

Querying the vector database for similar chunks:

```python
response = await vector_io_adapter.query_chunks(
    vector_db_id="research_db",
    query="What is machine learning?",
    params={"k": 5, "score_threshold": 0.7},
)
```

This process:
1. Converts the query text to an embedding
2. Performs a similarity search in the vector table
3. Retrieves the metadata for the most similar chunks
4. Returns chunks with similarity scores

## Implementation Details

### Vector Serialization

Embeddings are serialized to binary format for efficient storage:

```python
def serialize_vector(vector: List[float]) -> bytes:
    """Serialize a list of floats into a compact binary representation."""
    return struct.pack(f"{len(vector)}f", *vector)
```

This uses Python's `struct` module to pack floating-point values into a binary string.

### Chunk ID Generation

Each chunk is assigned a unique ID based on its content and document ID:

```python
def generate_chunk_id(document_id: str, chunk_text: str) -> str:
    """Generate a unique chunk ID using a hash of document ID and chunk text."""
    hash_input = f"{document_id}:{chunk_text}".encode("utf-8")
    return str(uuid.UUID(hashlib.md5(hash_input).hexdigest()))
```

This ensures that identical chunks from the same document have the same ID, preventing duplicates.

### Error Handling

The implementation includes robust error handling:

1. **Type Conversion**: Safely converts embedding values to float, with fallbacks for invalid types
2. **Connection Errors**: Handles SQLite connection issues gracefully
3. **Transaction Management**: Uses transactions with rollback on failure
4. **Logging**: Comprehensive logging of errors and operations

## Performance Considerations

### Batch Processing

Chunk insertion uses batch processing to improve performance:

```python
async def add_chunks(self, chunks: List[Chunk], embeddings: NDArray, batch_size: int = 500):
    # ...
    for i in range(0, len(chunks), batch_size):
        batch_chunks = chunks[i : i + batch_size]
        batch_embeddings = embeddings[i : i + batch_size]
        # Process batch...
```

This reduces the number of database transactions and improves throughput.

### Query Optimization

Vector queries are optimized using:

1. **Indexed Similarity Search**: The sqlite-vec extension provides efficient similarity search
2. **Score Thresholding**: Filters out low-relevance results
3. **Limit Parameter (k)**: Restricts the number of results returned

## Reproducibility Guidelines

To ensure reproducible research with vector databases:

1. **Use Consistent Parameters**:
   - Same embedding model and dimension
   - Same similarity threshold and k value
   - Same chunking strategy

2. **Document Database Configuration**:
   - Record the vector database provider used
   - Document all parameters in your research notes
   - Version control your configuration files

3. **Validate Results**:
   - Run queries multiple times to ensure consistent results
   - Compare results across different environments
   - Test with known inputs and expected outputs

## Example: Complete Vector Database Workflow

```python
import asyncio
from llama_stack.apis.vector_dbs import VectorDB
from llama_stack.apis.vector_io import Chunk
from llama_stack.utils.random_utils import set_random_seed

async def vector_db_workflow():
    # Set seed for reproducibility
    set_random_seed(42)
    
    # 1. Register vector database
    vector_db = VectorDB(
        identifier="research_experiment",
        embedding_model="all-MiniLM-L6-v2",
        embedding_dimension=384,
        metadata={"experiment": "text_classification"},
        provider_id="sqlite_vec",
    )
    await vector_io_adapter.register_vector_db(vector_db)
    
    # 2. Prepare chunks
    chunks = [
        Chunk(
            content="Machine learning is a subset of artificial intelligence.",
            metadata={"document_id": "doc1", "position": 0}
        ),
        Chunk(
            content="Neural networks are inspired by the human brain.",
            metadata={"document_id": "doc1", "position": 1}
        ),
        # More chunks...
    ]
    
    # 3. Insert chunks
    await vector_io_adapter.insert_chunks(
        vector_db_id="research_experiment",
        chunks=chunks,
    )
    
    # 4. Query the database
    response = await vector_io_adapter.query_chunks(
        vector_db_id="research_experiment",
        query="How do neural networks work?",
        params={"k": 3, "score_threshold": 0.7},
    )
    
    # 5. Process results
    for chunk, score in zip(response.chunks, response.scores):
        print(f"Score: {score:.4f} - {chunk.content}")
    
    # 6. Clean up (if needed)
    await vector_io_adapter.unregister_vector_db("research_experiment")

# Run the workflow
asyncio.run(vector_db_workflow())
```

By understanding these vector database operations and following the reproducibility guidelines, researchers can ensure consistent and reliable results in their work with Llama Stack.

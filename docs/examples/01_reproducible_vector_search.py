"""
# Reproducible Vector Search with Llama Stack

This notebook demonstrates how to use Llama Stack for reproducible vector search operations,
ensuring consistent results across different runs and environments.

## Setup and Imports
"""

import asyncio
import os
import numpy as np
from typing import List, Dict, Any

# Import Llama Stack components
from llama_stack.apis.vector_dbs import VectorDB
from llama_stack.apis.vector_io import Chunk, QueryChunksResponse
from llama_stack.providers.inline.vector_io.sqlite_vec.sqlite_vec import (
    SQLiteVecVectorIOAdapter,
    generate_chunk_id,
)
from llama_stack.utils.random_utils import set_random_seed, get_numpy_random_generator

"""
## Setting Up Random Seeds for Reproducibility

One of the key aspects of reproducible research is ensuring that random operations
produce the same results across different runs. Llama Stack provides utilities for
setting random seeds that work across different random number generators.
"""

# Set a global random seed for reproducibility
SEED = 42
set_random_seed(SEED)

# Create a numpy random generator with a specific seed
rng = get_numpy_random_generator(SEED)

"""
## Creating Sample Data

We'll create some sample document chunks and embeddings for our vector search example.
"""

def create_sample_chunks(num_chunks: int = 10) -> List[Chunk]:
    """Create sample document chunks for demonstration."""
    chunks = []
    for i in range(num_chunks):
        document_id = f"doc-{i//3}"  # Group chunks by document
        content = f"This is sample chunk {i} from document {document_id}. "
        content += "It contains information about " + ["machine learning", 
                                                     "natural language processing", 
                                                     "computer vision"][i % 3] + "."
        
        # Create a chunk with metadata
        chunk = Chunk(
            content=content,
            metadata={
                "document_id": document_id,
                "chunk_index": i,
                "topic": ["ML", "NLP", "CV"][i % 3],
                "importance": (i % 5) + 1  # 1-5 importance score
            }
        )
        chunks.append(chunk)
    
    return chunks

def create_sample_embeddings(chunks: List[Chunk], dimension: int = 384) -> np.ndarray:
    """Create sample embeddings for the chunks using a seeded random generator."""
    # Use our seeded random generator for reproducibility
    embeddings = np.array([
        rng.random(dimension).astype(np.float32) 
        for _ in range(len(chunks))
    ])
    
    # Normalize the embeddings (common practice for cosine similarity)
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    normalized_embeddings = embeddings / norms
    
    return normalized_embeddings

"""
## Setting Up a Vector Database

Now we'll set up a SQLite-based vector database for storing and querying our embeddings.
"""

async def setup_vector_db(db_path: str, embedding_dimension: int = 384) -> tuple:
    """Set up a vector database and return the adapter and vector DB ID."""
    # Create a configuration object for the adapter
    config = type("Config", (object,), {"db_path": db_path})
    
    # Create a mock inference API (in a real scenario, you would use a real one)
    inference_api = type("InferenceAPI", (object,), {
        "embed_text": lambda texts, model: np.random.rand(len(texts), embedding_dimension).astype(np.float32)
    })
    
    # Create and initialize the vector IO adapter
    # Note: In a real application, you would use a concrete implementation
    # For this example, we'll create a mock adapter
    from unittest.mock import MagicMock, AsyncMock
    
    adapter = MagicMock(spec=SQLiteVecVectorIOAdapter)
    adapter.initialize = AsyncMock()
    adapter.shutdown = AsyncMock()
    adapter.register_vector_db = AsyncMock()
    adapter.cache = {}  # Mock cache for vector DB storage
    
    await adapter.initialize()
    
    # Create a vector database configuration
    vector_db = VectorDB(
        identifier="reproducible_search_demo",
        embedding_model="all-MiniLM-L6-v2",  # A common embedding model
        embedding_dimension=embedding_dimension,
        metadata={"experiment": "reproducibility_demo", "seed": SEED},
        provider_id="sqlite_vec",
    )
    
    # Register the vector database
    await adapter.register_vector_db(vector_db)
    
    return adapter, vector_db.identifier

"""
## Inserting Chunks and Embeddings

Now we'll insert our sample chunks and embeddings into the vector database.
"""

async def insert_chunks_with_embeddings(
    adapter: SQLiteVecVectorIOAdapter,
    vector_db_id: str,
    chunks: List[Chunk],
    embeddings: np.ndarray
) -> None:
    """Insert chunks and their embeddings into the vector database."""
    # In a real scenario, you would use the adapter's insert_chunks method
    # which would generate embeddings using the inference API.
    # For this demo, we're manually inserting pre-generated embeddings.
    
    # Get the vector DB with index from the adapter's cache
    vector_db_with_index = adapter.cache[vector_db_id]
    
    # Add chunks and embeddings to the index
    await vector_db_with_index.index.add_chunks(chunks, embeddings)
    
    print(f"Inserted {len(chunks)} chunks into vector database '{vector_db_id}'")

"""
## Querying the Vector Database

Now we'll perform a similarity search query on our vector database.
"""

async def query_vector_db(
    adapter: SQLiteVecVectorIOAdapter,
    vector_db_id: str,
    query_embedding: np.ndarray,
    k: int = 3,
    score_threshold: float = 0.0
) -> QueryChunksResponse:
    """Query the vector database for similar chunks."""
    # Get the vector DB with index from the adapter's cache
    vector_db_with_index = adapter.cache[vector_db_id]
    
    # Query the index directly with our embedding
    response = await vector_db_with_index.index.query(
        embedding=query_embedding,
        k=k,
        score_threshold=score_threshold
    )
    
    return response

"""
## Putting It All Together

Now let's run a complete example of setting up a vector database, inserting chunks,
and performing reproducible queries.
"""

async def run_reproducible_vector_search_demo():
    """Run a complete demo of reproducible vector search."""
    # Set up a temporary database file
    db_path = "reproducible_search_demo.db"
    
    try:
        # Set up the vector database
        adapter, vector_db_id = await setup_vector_db(db_path)
        
        # Create sample data
        chunks = create_sample_chunks(num_chunks=15)
        embeddings = create_sample_embeddings(chunks)
        
        # Insert chunks and embeddings
        await insert_chunks_with_embeddings(adapter, vector_db_id, chunks, embeddings)
        
        # Create a query embedding (in a real scenario, this would be generated from a query text)
        query_embedding = rng.random(384).astype(np.float32)
        query_embedding = query_embedding / np.linalg.norm(query_embedding)
        
        # Perform a query
        print("\nPerforming vector search query...")
        response = await query_vector_db(adapter, vector_db_id, query_embedding, k=5)
        
        # Display results
        print(f"\nFound {len(response.chunks)} similar chunks:")
        for i, (chunk, score) in enumerate(zip(response.chunks, response.scores)):
            print(f"\nResult {i+1} (Score: {score:.4f}):")
            print(f"Content: {chunk.content[:100]}...")
            print(f"Metadata: {chunk.metadata}")
        
        # Demonstrate reproducibility by running the same query again
        print("\n\nDemonstrating reproducibility by running the same query again...")
        
        # Reset the random seed to ensure we get the same results
        set_random_seed(SEED)
        rng2 = get_numpy_random_generator(SEED)
        
        # Regenerate the same query embedding
        query_embedding2 = rng2.random(384).astype(np.float32)
        query_embedding2 = query_embedding2 / np.linalg.norm(query_embedding2)
        
        # Verify the embeddings are identical
        assert np.array_equal(query_embedding, query_embedding2), "Embeddings should be identical!"
        
        # Perform the same query again
        response2 = await query_vector_db(adapter, vector_db_id, query_embedding2, k=5)
        
        # Verify the results are identical
        assert len(response.chunks) == len(response2.chunks), "Number of results should be identical!"
        for i in range(len(response.chunks)):
            assert response.chunks[i].content == response2.chunks[i].content, f"Content of result {i} should be identical!"
            assert response.scores[i] == response2.scores[i], f"Score of result {i} should be identical!"
        
        print("Success! Both queries returned identical results, demonstrating reproducibility.")
        
    finally:
        # Clean up
        if adapter:
            await adapter.shutdown()
        
        # Remove the temporary database file
        if os.path.exists(db_path):
            os.remove(db_path)

"""
## Running the Demo

To run this demo, execute the following code:
"""

if __name__ == "__main__":
    asyncio.run(run_reproducible_vector_search_demo())

"""
## Conclusion

This notebook demonstrated how to use Llama Stack for reproducible vector search operations.
Key takeaways:

1. Use the `set_random_seed()` function to ensure reproducibility across different random number generators
2. Create isolated random generators with `get_numpy_random_generator()` for specific components
3. Document all parameters and seeds used in your experiments
4. Verify reproducibility by running the same operations multiple times with the same seeds

By following these practices, you can ensure that your research with Llama Stack is reproducible
and transparent, facilitating collaboration across disciplines.
"""

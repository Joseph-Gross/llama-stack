# Embedding Generation in Llama Stack

This document explains the embedding generation process in Llama Stack, focusing on how text is converted to vector representations for use in vector databases and similarity search.

## Overview

Embeddings are numerical representations of text that capture semantic meaning in a way that allows for efficient similarity comparison. In Llama Stack, embeddings are used primarily for:

1. Storing document chunks in vector databases
2. Performing similarity searches for retrieval-augmented generation (RAG)
3. Comparing semantic similarity between texts

## Embedding Models

Llama Stack supports various embedding models, with the default being "all-MiniLM-L6-v2" from the Sentence Transformers library. This model produces 384-dimensional embeddings that balance quality and efficiency.

### Supported Models

| Model Name | Dimensions | Characteristics | Best For |
|------------|------------|-----------------|----------|
| all-MiniLM-L6-v2 | 384 | Fast, general-purpose | General text similarity |
| all-mpnet-base-v2 | 768 | Higher quality, slower | Research requiring higher precision |
| paraphrase-multilingual-MiniLM-L12-v2 | 384 | Multilingual support | Multilingual applications |

## Embedding Generation Process

### 1. Text Preprocessing

Before generating embeddings, text undergoes preprocessing:

- **Normalization**: Converting to lowercase, removing extra whitespace
- **Tokenization**: Breaking text into tokens (words, subwords)
- **Special Token Handling**: Adding model-specific tokens (e.g., [CLS], [SEP])

### 2. Model Inference

The preprocessed text is passed through the embedding model:

```python
# Simplified example of embedding generation
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")
embedding = model.encode("This is a sample text", convert_to_numpy=True)
```

The model produces a fixed-dimension vector (e.g., 384 dimensions for all-MiniLM-L6-v2).

### 3. Post-processing

Embeddings may undergo post-processing:

- **Normalization**: L2 normalization to ensure consistent magnitude
- **Type Conversion**: Converting to float32 for compatibility
- **Error Handling**: Handling NaN values or other anomalies

## Implementation in Llama Stack

### Embedding Generation in Vector Databases

In Llama Stack, embedding generation is typically handled by the `VectorDBWithIndex` class, which uses an inference API to generate embeddings for chunks:

```python
class VectorDBWithIndex:
    def __init__(self, vector_db: VectorDB, index: EmbeddingIndex, inference_api: Any):
        self.vector_db = vector_db
        self.index = index
        self.inference_api = inference_api

    async def insert_chunks(self, chunks: List[Chunk]) -> None:
        # Generate embeddings using the inference API
        embeddings = await self._generate_embeddings(chunks)
        # Insert chunks and embeddings into the index
        await self.index.add_chunks(chunks, embeddings)

    async def _generate_embeddings(self, chunks: List[Chunk]) -> NDArray:
        # Extract text content from chunks
        texts = [chunk.content for chunk in chunks]
        # Generate embeddings using the inference API
        embeddings = await self.inference_api.generate_embeddings(
            texts, model=self.vector_db.embedding_model
        )
        return embeddings
```

### Error Handling and Robustness

Llama Stack includes robust error handling for embedding generation:

1. **Type Conversion**: Safely converts embedding values to float
   ```python
   # Example from SQLiteVecIndex.query
   float_list = []
   for val in emb_list:
       try:
           # Explicitly convert to float with a safer approach
           if isinstance(val, (int, float)):
               float_list.append(float(val))
           elif isinstance(val, str):
               float_list.append(float(val.strip()))
           else:
               # For other types, use fallback
               float_list.append(0.0)
       except (ValueError, TypeError):
           # If conversion fails, use 0.0 as a fallback
           float_list.append(0.0)
   ```

2. **Dimension Validation**: Ensures embeddings have the expected dimension
3. **Null Handling**: Handles None values and empty inputs gracefully

## Parameters and Configuration

### Key Parameters

| Parameter | Description | Default | Impact |
|-----------|-------------|---------|--------|
| embedding_model | Name of the embedding model | "all-MiniLM-L6-v2" | Affects embedding quality and dimension |
| embedding_dimension | Size of embedding vectors | 384 | Must match the model's output dimension |
| batch_size | Number of texts to embed at once | 32 | Affects memory usage and throughput |
| normalize_embeddings | Whether to L2-normalize embeddings | True | Affects similarity calculation method |

### Configuration Example

```python
from llama_stack.apis.vector_dbs import VectorDB

# Configure a vector database with specific embedding parameters
vector_db = VectorDB(
    identifier="research_db",
    embedding_model="all-mpnet-base-v2",  # Higher quality model
    embedding_dimension=768,  # Matching the model's dimension
    metadata={
        "normalize_embeddings": True,
        "batch_size": 16,  # Smaller batch size for larger model
    },
    provider_id="sqlite_vec",
)
```

## Reproducibility Guidelines

To ensure reproducible embedding generation:

1. **Use Fixed Seeds**:
   ```python
   from llama_stack.utils.random_utils import set_random_seed
   
   # Set seed before generating embeddings
   set_random_seed(42)
   ```

2. **Document Model Version**:
   - Record the exact model name and version
   - Note any custom preprocessing steps

3. **Consistent Parameters**:
   - Use the same batch size and normalization settings
   - Maintain consistent preprocessing steps

4. **Validate Embeddings**:
   - Check embedding dimensions match expectations
   - Verify similar texts produce similar embeddings

## Example: Complete Embedding Workflow

```python
import numpy as np
from llama_stack.utils.random_utils import set_random_seed
from sentence_transformers import SentenceTransformer

def generate_reproducible_embeddings(texts, model_name="all-MiniLM-L6-v2", seed=42):
    """Generate reproducible embeddings for a list of texts."""
    # Set seed for reproducibility
    set_random_seed(seed)
    
    # Load the model
    model = SentenceTransformer(model_name)
    
    # Document parameters
    params = {
        "model": model_name,
        "seed": seed,
        "normalize": True,
        "dimension": model.get_sentence_embedding_dimension(),
    }
    print(f"Embedding parameters: {params}")
    
    # Generate embeddings
    embeddings = model.encode(texts, convert_to_numpy=True)
    
    # Validate embeddings
    expected_dim = params["dimension"]
    for i, emb in enumerate(embeddings):
        assert len(emb) == expected_dim, f"Embedding {i} has wrong dimension: {len(emb)} != {expected_dim}"
    
    return embeddings

# Example usage
texts = [
    "Machine learning is a subset of artificial intelligence.",
    "Neural networks are inspired by the human brain.",
    "Natural language processing deals with text data.",
]

embeddings = generate_reproducible_embeddings(texts)
```

By following these guidelines and understanding the embedding generation process, researchers can ensure consistent and reliable results in their work with Llama Stack.

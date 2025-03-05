# Data Preprocessing in Llama Stack

This documentation explains the data preprocessing steps and parameters used in Llama Stack, focusing on vector databases, embedding generation, and document handling. Understanding these preprocessing steps is essential for ensuring reproducibility and facilitating interdisciplinary collaboration.

## Table of Contents

1. [Document Chunking](#document-chunking)
2. [Embedding Generation](#embedding-generation)
3. [Vector Database Operations](#vector-database-operations)
4. [Preprocessing Parameters](#preprocessing-parameters)
5. [Reproducibility Guidelines](#reproducibility-guidelines)

## Document Chunking

Document chunking is the process of breaking down large documents into smaller, manageable pieces for efficient storage and retrieval in vector databases.

### Chunking Process

1. **Input**: Documents with text content
2. **Processing**:
   - Documents are split into smaller chunks based on configurable parameters
   - Each chunk is assigned metadata including its source document ID and position
3. **Output**: A list of `Chunk` objects containing content and metadata

### Key Components

- **Chunk Class** (`llama_stack/apis/vector_io/vector_io.py`): Defines the structure of document chunks
  ```python
  class Chunk(BaseModel):
      content: InterleavedContent
      metadata: Dict[str, Any] = Field(default_factory=dict)
  ```

- **Chunk ID Generation** (`llama_stack/providers/inline/vector_io/sqlite_vec/sqlite_vec.py`): Creates unique identifiers for chunks
  ```python
  def generate_chunk_id(document_id: str, chunk_text: str) -> str:
      """Generate a unique chunk ID using a hash of document ID and chunk text."""
      hash_input = f"{document_id}:{chunk_text}".encode("utf-8")
      return str(uuid.UUID(hashlib.md5(hash_input).hexdigest()))
  ```

## Embedding Generation

Embedding generation converts text chunks into numerical vector representations that capture semantic meaning, enabling similarity-based retrieval.

### Embedding Process

1. **Input**: Text chunks
2. **Processing**:
   - Text is tokenized and processed through an embedding model
   - The model generates fixed-dimension vector representations
3. **Output**: Numerical embeddings (typically float32 arrays)

### Key Components

- **VectorDBWithIndex** (`llama_stack/providers/utils/memory/vector_store.py`): Handles embedding generation via inference API
- **Embedding Models**: Sentence transformers like "all-MiniLM-L6-v2" are commonly used
- **Embedding Dimension**: Typically 384 for models like "all-MiniLM-L6-v2"

## Vector Database Operations

Vector database operations include storing, indexing, and querying embeddings for efficient similarity search.

### Storage Process

1. **Input**: Chunks and their embeddings
2. **Processing**:
   - Embeddings are serialized and stored in a vector database
   - Metadata is stored separately but linked to embeddings
3. **Output**: Indexed database ready for similarity queries

### Query Process

1. **Input**: Query text or embedding
2. **Processing**:
   - Query is converted to an embedding (if text)
   - Vector similarity search is performed
   - Results are ranked by similarity score
3. **Output**: Ranked list of relevant chunks with similarity scores

### Key Components

- **SQLiteVecIndex** (`llama_stack/providers/inline/vector_io/sqlite_vec/sqlite_vec.py`): Implements vector storage and retrieval
  ```python
  class SQLiteVecIndex(EmbeddingIndex):
      """
      An index implementation that stores embeddings in a SQLite virtual table using sqlite-vec.
      Two tables are used:
        - A metadata table (chunks_{bank_id}) that holds the chunk JSON.
        - A virtual table (vec_chunks_{bank_id}) that holds the serialized vector.
      """
  ```

- **Vector Serialization** (`llama_stack/providers/inline/vector_io/sqlite_vec/sqlite_vec.py`): Converts embeddings to binary format
  ```python
  def serialize_vector(vector: List[float]) -> bytes:
      """Serialize a list of floats into a compact binary representation."""
      return struct.pack(f"{len(vector)}f", *vector)
  ```

## Preprocessing Parameters

Understanding and configuring these parameters is crucial for reproducible research:

### Chunking Parameters

| Parameter | Description | Typical Value | Impact |
|-----------|-------------|---------------|--------|
| Chunk Size | Number of tokens/characters per chunk | 512-1024 tokens | Affects retrieval granularity and context window |
| Overlap | Number of tokens/characters overlapping between chunks | 10-20% of chunk size | Prevents context loss at chunk boundaries |

### Embedding Parameters

| Parameter | Description | Typical Value | Impact |
|-----------|-------------|---------------|--------|
| Embedding Model | Model used to generate embeddings | "all-MiniLM-L6-v2" | Affects semantic understanding and vector quality |
| Embedding Dimension | Size of the embedding vectors | 384 | Affects storage requirements and search performance |
| Normalization | Whether embeddings are normalized | True | Affects similarity calculation (cosine vs. dot product) |

### Vector Database Parameters

| Parameter | Description | Typical Value | Impact |
|-----------|-------------|---------------|--------|
| k | Number of results to return in queries | 3-10 | Affects recall and processing time |
| Score Threshold | Minimum similarity score for results | 0.0-0.7 | Affects precision (higher = more precise) |
| Batch Size | Number of chunks to process at once | 500 | Affects memory usage and processing time |

## Reproducibility Guidelines

To ensure reproducible research with Llama Stack's vector operations:

1. **Document Parameters**: Always record all preprocessing parameters used in your experiments
2. **Use Fixed Seeds**: Set random seeds for embedding models when applicable
3. **Version Control**: Track the versions of embedding models and libraries used
4. **Standardize Preprocessing**: Use consistent preprocessing steps across experiments
5. **Validate Results**: Verify that similar inputs produce similar embeddings and query results

### Example: Reproducible Vector Database Setup

```python
from llama_stack.apis.vector_dbs import VectorDB
from llama_stack.utils.random_utils import set_random_seed

# Set a fixed seed for reproducibility
set_random_seed(42)

# Create a vector database with explicit parameters
vector_db = VectorDB(
    identifier="research_experiment_1",
    embedding_model="all-MiniLM-L6-v2",
    embedding_dimension=384,
    metadata={"experiment": "text_classification", "date": "2025-03-05"},
    provider_id="sqlite_vec",
)

# Document the parameters used
parameters = {
    "chunk_size": 512,
    "chunk_overlap": 50,
    "embedding_model": "all-MiniLM-L6-v2",
    "embedding_dimension": 384,
    "k": 5,
    "score_threshold": 0.7,
    "batch_size": 500,
}
```

By following these guidelines and understanding the preprocessing steps, researchers from different disciplines can collaborate effectively and ensure that their experiments are reproducible.

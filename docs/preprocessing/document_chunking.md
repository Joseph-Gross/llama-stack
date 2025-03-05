# Document Chunking in Llama Stack

This document explains the document chunking process in Llama Stack, focusing on how documents are split into smaller chunks for efficient storage and retrieval in vector databases.

## Overview

Document chunking is the process of breaking down large documents into smaller, manageable pieces. This is essential for:

1. **Efficient Retrieval**: Smaller chunks allow for more precise retrieval of relevant information
2. **Context Management**: Chunks fit within the context window of language models
3. **Granular Similarity**: Enables more granular similarity matching

## Chunking Process

### 1. Document Preparation

Before chunking, documents typically undergo preparation:

- **Cleaning**: Removing irrelevant content (e.g., headers, footers)
- **Normalization**: Standardizing text format (e.g., whitespace, encoding)
- **Metadata Extraction**: Capturing document metadata (e.g., title, author, date)

### 2. Chunking Strategies

Llama Stack supports various chunking strategies:

#### a. Fixed-Size Chunking

Divides documents into chunks of approximately equal size:

```python
def fixed_size_chunking(text, chunk_size=1000, overlap=100):
    """Split text into chunks of approximately equal size with overlap."""
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        # Adjust end to avoid cutting words
        if end < len(text):
            # Find the last space before the end
            while end > start and text[end] != ' ':
                end -= 1
        chunks.append(text[start:end])
        start = end - overlap
    return chunks
```

#### b. Semantic Chunking

Divides documents based on semantic boundaries (e.g., paragraphs, sections):

```python
def semantic_chunking(text):
    """Split text based on paragraph boundaries."""
    # Split on double newlines (paragraph boundaries)
    paragraphs = text.split('\n\n')
    # Filter out empty paragraphs
    return [p.strip() for p in paragraphs if p.strip()]
```

#### c. Hybrid Chunking

Combines fixed-size and semantic approaches:

```python
def hybrid_chunking(text, max_chunk_size=1000):
    """Split text based on semantic boundaries, but ensure chunks don't exceed max size."""
    paragraphs = text.split('\n\n')
    chunks = []
    current_chunk = ""
    
    for paragraph in paragraphs:
        if len(current_chunk) + len(paragraph) <= max_chunk_size:
            current_chunk += paragraph + "\n\n"
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = paragraph + "\n\n"
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks
```

### 3. Chunk Processing

After splitting, each chunk is processed:

- **Metadata Assignment**: Adding source document ID, position, etc.
- **Chunk ID Generation**: Creating unique identifiers for each chunk
- **Validation**: Ensuring chunks meet minimum/maximum size requirements

## Implementation in Llama Stack

In Llama Stack, chunks are represented by the `Chunk` class:

```python
class Chunk(BaseModel):
    content: InterleavedContent
    metadata: Dict[str, Any] = Field(default_factory=dict)
```

Each chunk contains:
- **Content**: The text or interleaved content of the chunk
- **Metadata**: Information about the chunk (e.g., document ID, position)

### Chunk ID Generation

Unique IDs are generated for each chunk based on content and document ID:

```python
def generate_chunk_id(document_id: str, chunk_text: str) -> str:
    """Generate a unique chunk ID using a hash of document ID and chunk text."""
    hash_input = f"{document_id}:{chunk_text}".encode("utf-8")
    return str(uuid.UUID(hashlib.md5(hash_input).hexdigest()))
```

This ensures that identical chunks from the same document have the same ID, preventing duplicates.

## Parameters and Configuration

### Key Parameters

| Parameter | Description | Typical Value | Impact |
|-----------|-------------|---------------|--------|
| chunk_size | Size of each chunk (characters/tokens) | 512-1024 tokens | Affects retrieval granularity and context window |
| chunk_overlap | Overlap between consecutive chunks | 10-20% of chunk size | Prevents context loss at chunk boundaries |
| chunking_strategy | Method used for splitting documents | "fixed", "semantic", "hybrid" | Affects chunk boundaries and coherence |
| min_chunk_size | Minimum size for a valid chunk | 50-100 tokens | Filters out too-small chunks |

### Configuration Example

```python
chunking_config = {
    "strategy": "hybrid",
    "max_chunk_size": 800,
    "min_chunk_size": 100,
    "overlap": 50,
    "split_on": ["\n\n", "\n### ", "\n## ", "\n# "],  # Split on these markers
    "keep_separator": True,  # Keep the separator with the chunk
}
```

## Reproducibility Guidelines

To ensure reproducible document chunking:

1. **Consistent Parameters**:
   - Use the same chunking strategy and parameters
   - Document all parameters in your research notes

2. **Preprocessing Standardization**:
   - Apply the same text cleaning and normalization steps
   - Handle special characters and formatting consistently

3. **Validate Chunks**:
   - Verify chunk boundaries are consistent
   - Check that chunk IDs are generated consistently

4. **Document the Process**:
   - Record the exact chunking algorithm used
   - Note any special handling for specific document types

## Example: Complete Chunking Workflow

```python
from typing import Dict, List, Any
from pydantic import BaseModel
import hashlib
import uuid

class Chunk(BaseModel):
    content: str
    metadata: Dict[str, Any]

def generate_chunk_id(document_id: str, chunk_text: str) -> str:
    """Generate a unique chunk ID using a hash of document ID and chunk text."""
    hash_input = f"{document_id}:{chunk_text}".encode("utf-8")
    return str(uuid.UUID(hashlib.md5(hash_input).hexdigest()))

def chunk_document(
    document_text: str,
    document_id: str,
    config: Dict[str, Any]
) -> List[Chunk]:
    """
    Chunk a document according to the specified configuration.
    
    Args:
        document_text: The text of the document to chunk
        document_id: Unique identifier for the document
        config: Chunking configuration parameters
        
    Returns:
        List of Chunk objects
    """
    # Extract configuration parameters
    strategy = config.get("strategy", "fixed")
    max_chunk_size = config.get("max_chunk_size", 1000)
    min_chunk_size = config.get("min_chunk_size", 100)
    overlap = config.get("overlap", 50)
    
    # Apply chunking strategy
    if strategy == "fixed":
        raw_chunks = fixed_size_chunking(document_text, max_chunk_size, overlap)
    elif strategy == "semantic":
        raw_chunks = semantic_chunking(document_text)
    elif strategy == "hybrid":
        raw_chunks = hybrid_chunking(document_text, max_chunk_size)
    else:
        raise ValueError(f"Unknown chunking strategy: {strategy}")
    
    # Process chunks
    chunks = []
    for i, text in enumerate(raw_chunks):
        # Skip chunks that are too small
        if len(text) < min_chunk_size:
            continue
            
        # Create chunk with metadata
        chunk = Chunk(
            content=text,
            metadata={
                "document_id": document_id,
                "chunk_index": i,
                "strategy": strategy,
                "chunk_size": len(text),
            }
        )
        chunks.append(chunk)
    
    # Document the chunking process
    print(f"Document {document_id} chunked into {len(chunks)} chunks using {strategy} strategy")
    print(f"Average chunk size: {sum(len(c.content) for c in chunks) / len(chunks) if chunks else 0}")
    
    return chunks

# Example usage
document = "This is a sample document.\n\nIt contains multiple paragraphs.\n\nEach paragraph should ideally become its own chunk."
document_id = "doc-123"

config = {
    "strategy": "semantic",
    "min_chunk_size": 10,
}

chunks = chunk_document(document, document_id, config)
```

By following these guidelines and understanding the document chunking process, researchers can ensure consistent and reliable results in their work with Llama Stack.

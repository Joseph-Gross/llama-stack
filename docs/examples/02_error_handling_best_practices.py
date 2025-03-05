"""
# Error Handling Best Practices with Llama Stack

This notebook demonstrates best practices for error handling in Llama Stack,
focusing on robust type conversion, graceful failure, and comprehensive logging.

## Setup and Imports
"""

import asyncio
import logging
import os
import tempfile
from typing import List, Dict, Any, Optional, Union, Tuple

import numpy as np

from llama_stack.apis.vector_dbs import VectorDB
from llama_stack.apis.vector_io import Chunk, QueryChunksResponse
from llama_stack.utils.random_utils import set_random_seed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("error_handling_demo")

"""
## 1. Robust Type Conversion

One common source of errors in data processing is handling unexpected input types.
This section demonstrates robust type conversion techniques.
"""

def robust_float_conversion(value: Any) -> float:
    """
    Convert a value to float with robust error handling.
    
    Args:
        value: Any value to convert to float
        
    Returns:
        Converted float value or 0.0 if conversion fails
    """
    try:
        # Handle different input types
        if isinstance(value, (int, float)):
            return float(value)
        elif isinstance(value, str):
            return float(value.strip())
        elif value is None:
            logger.warning("Received None value for float conversion, using default 0.0")
            return 0.0
        else:
            logger.warning(f"Unexpected type {type(value)} for float conversion, using default 0.0")
            return 0.0
    except (ValueError, TypeError) as e:
        logger.warning(f"Error converting value '{value}' to float: {e}")
        return 0.0

def robust_list_conversion(values: Any, dimension: int) -> List[float]:
    """
    Convert a list of values to a list of floats with robust error handling.
    
    Args:
        values: List of values to convert
        dimension: Expected dimension of the output list
        
    Returns:
        List of floats with the specified dimension
    """
    result = []
    
    # Handle case where input is not iterable
    if not hasattr(values, '__iter__') or isinstance(values, str):
        logger.warning(f"Expected iterable, got {type(values)}. Creating zero vector.")
        return [0.0] * dimension
    
    # Convert each value
    for val in values:
        result.append(robust_float_conversion(val))
    
    # Handle dimension mismatch
    if len(result) != dimension:
        logger.warning(f"Dimension mismatch: got {len(result)}, expected {dimension}")
        if len(result) < dimension:
            # Pad with zeros
            result.extend([0.0] * (dimension - len(result)))
        else:
            # Truncate
            result = result[:dimension]
    
    return result

"""
## 2. Graceful Failure and Recovery

This section demonstrates how to implement graceful failure and recovery mechanisms.
"""

async def safe_vector_db_operation(
    operation_name: str,
    operation_func: Any,  # Use Any instead of callable to avoid type issues
    fallback_value: Any = None,
    max_retries: int = 3,
    retry_delay: float = 1.0,
    *args, **kwargs
) -> Any:
    """
    Execute a vector database operation with retry logic and graceful failure.
    
    Args:
        operation_name: Name of the operation for logging
        operation_func: Function to execute
        fallback_value: Value to return if all retries fail
        max_retries: Maximum number of retry attempts
        retry_delay: Delay between retries in seconds
        *args, **kwargs: Arguments to pass to the operation function
        
    Returns:
        Result of the operation or fallback value if all retries fail
    """
    for attempt in range(max_retries):
        try:
            logger.info(f"Executing {operation_name} (attempt {attempt+1}/{max_retries})")
            result = await operation_func(*args, **kwargs)
            logger.info(f"Successfully executed {operation_name}")
            return result
        except Exception as e:
            logger.error(f"Error executing {operation_name} (attempt {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
            else:
                logger.warning(f"All retry attempts for {operation_name} failed, using fallback value")
                return fallback_value

"""
## 3. Comprehensive Logging

This section demonstrates comprehensive logging practices for tracking operations
and diagnosing issues.
"""

class LoggedOperation:
    """Context manager for logging operations with timing and outcome tracking."""
    
    def __init__(self, operation_name: str, logger: logging.Logger):
        self.operation_name = operation_name
        self.logger = logger
        self.start_time = None
    
    async def __aenter__(self):
        import time
        self.start_time = time.time()
        self.logger.info(f"Starting operation: {self.operation_name}")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        import time
        # Ensure start_time is not None before subtraction
        duration = time.time() - (self.start_time or time.time())
        
        if exc_type is None:
            self.logger.info(f"Completed operation: {self.operation_name} in {duration:.2f}s")
        else:
            self.logger.error(f"Failed operation: {self.operation_name} after {duration:.2f}s")
            self.logger.error(f"Error: {exc_type.__name__}: {exc_val}")
            # Log traceback for debugging
            import traceback
            self.logger.debug(f"Traceback: {''.join(traceback.format_tb(exc_tb))}")
        
        # Don't suppress exceptions
        return False

"""
## 4. Practical Example: Robust Vector Database Operations

Now let's put these techniques together in a practical example of robust vector
database operations.
"""

class RobustVectorDBClient:
    """A client for vector database operations with robust error handling."""
    
    def __init__(self, db_path: str, embedding_dimension: int = 384):
        self.db_path = db_path
        self.embedding_dimension = embedding_dimension
        self.adapter = None
        self.vector_db_id = "robust_vector_db"
        self.logger = logging.getLogger("RobustVectorDBClient")
    
    async def initialize(self) -> bool:
        """Initialize the vector database with robust error handling."""
        async with LoggedOperation("initialize_vector_db", self.logger):
            try:
                # Import here to avoid circular imports
                from llama_stack.providers.inline.vector_io.sqlite_vec.sqlite_vec import (
                    SQLiteVecVectorIOAdapter,
                )
                
                # Create a configuration object
                config = type("Config", (object,), {"db_path": self.db_path})
                
                # Create a mock inference API
                inference_api = type("InferenceAPI", (object,), {
                    "embed_text": lambda texts, model: np.random.rand(len(texts), self.embedding_dimension).astype(np.float32)
                })
                
                # Create and initialize the adapter
                # Note: In a real application, you would use a concrete implementation
                # For this example, we'll create a mock adapter
                from unittest.mock import MagicMock, AsyncMock
                
                self.adapter = MagicMock(spec=SQLiteVecVectorIOAdapter)
                self.adapter.initialize = AsyncMock()
                self.adapter.shutdown = AsyncMock()
                self.adapter.register_vector_db = AsyncMock()
                self.adapter.insert_chunks = AsyncMock(return_value=True)
                self.adapter.query_chunks = AsyncMock(return_value=QueryChunksResponse(chunks=[], scores=[]))
                self.adapter.cache = {}  # Mock cache for vector DB storage
                
                await self.adapter.initialize()
                
                # Register a vector database
                vector_db = VectorDB(
                    identifier=self.vector_db_id,
                    embedding_model="all-MiniLM-L6-v2",
                    embedding_dimension=self.embedding_dimension,
                    metadata={"client": "RobustVectorDBClient"},
                    provider_id="sqlite_vec",
                )
                
                await self.adapter.register_vector_db(vector_db)
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to initialize vector database: {e}")
                return False
    
    async def shutdown(self) -> None:
        """Shut down the vector database client."""
        if self.adapter:
            try:
                await self.adapter.shutdown()
                self.logger.info("Vector database client shut down successfully")
            except Exception as e:
                self.logger.error(f"Error shutting down vector database client: {e}")
    
    async def insert_chunks(self, chunks: List[Chunk]) -> bool:
        """Insert chunks into the vector database with robust error handling."""
        if not self.adapter:
            self.logger.error("Vector database client not initialized")
            return False
        
        # Filter out invalid chunks
        valid_chunks = []
        for i, chunk in enumerate(chunks):
            if not chunk.content:
                self.logger.warning(f"Skipping chunk {i}: empty content")
                continue
            if not chunk.metadata or "document_id" not in chunk.metadata:
                self.logger.warning(f"Skipping chunk {i}: missing document_id in metadata")
                continue
            valid_chunks.append(chunk)
        
        self.logger.info(f"Filtered {len(chunks) - len(valid_chunks)} invalid chunks")
        
        if not valid_chunks:
            self.logger.warning("No valid chunks to insert")
            return False
        
        return await safe_vector_db_operation(
            "insert_chunks",
            self.adapter.insert_chunks,
            fallback_value=False,
            vector_db_id=self.vector_db_id,
            chunks=valid_chunks,
        )
    
    async def query_chunks(
        self, 
        query_embedding: Union[List[float], np.ndarray],
        k: int = 3,
        score_threshold: float = 0.0
    ) -> Tuple[List[Chunk], List[float]]:
        """Query chunks from the vector database with robust error handling."""
        if not self.adapter:
            self.logger.error("Vector database client not initialized")
            return [], []
        
        # Ensure query embedding has the correct format
        if isinstance(query_embedding, list):
            query_embedding = robust_list_conversion(query_embedding, self.embedding_dimension)
            query_embedding = np.array(query_embedding, dtype=np.float32)
        elif isinstance(query_embedding, np.ndarray):
            if query_embedding.shape != (self.embedding_dimension,):
                self.logger.warning(f"Query embedding has incorrect shape: {query_embedding.shape}")
                query_embedding = np.zeros(self.embedding_dimension, dtype=np.float32)
        else:
            self.logger.error(f"Unsupported query embedding type: {type(query_embedding)}")
            return [], []
        
        # Execute the query with robust error handling
        response = await safe_vector_db_operation(
            "query_chunks",
            self.adapter.query_chunks,
            fallback_value=QueryChunksResponse(chunks=[], scores=[]),
            vector_db_id=self.vector_db_id,
            embedding=query_embedding,
            k=k,
            score_threshold=score_threshold,
        )
        
        return response.chunks, response.scores

"""
## 5. Demonstration

Now let's demonstrate these error handling techniques in action.
"""

async def run_error_handling_demo():
    """Run a demonstration of error handling best practices."""
    # Set a random seed for reproducibility
    set_random_seed(42)
    
    # Create a temporary database file
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp_file:
        db_path = temp_file.name
    
    client = None
    try:
        logger.info("Starting error handling demonstration")
        
        # Initialize the vector database client
        client = RobustVectorDBClient(db_path)
        success = await client.initialize()
        
        if not success:
            logger.error("Failed to initialize vector database client")
            return
        
        # Create sample chunks with some invalid data
        chunks = [
            # Valid chunks
            Chunk(content="This is a valid chunk", metadata={"document_id": "doc1"}),
            Chunk(content="Another valid chunk", metadata={"document_id": "doc1"}),
            # Invalid chunks
            Chunk(content="", metadata={"document_id": "doc2"}),  # Empty content
            Chunk(content="Missing document ID", metadata={}),  # Missing document_id
            Chunk(content=None, metadata={"document_id": "doc3"}),  # None content
        ]
        
        # Insert chunks
        logger.info("Inserting chunks with mixed validity")
        success = await client.insert_chunks(chunks)
        
        if not success:
            logger.error("Failed to insert chunks")
            return
        
        # Demonstrate robust type conversion
        logger.info("Demonstrating robust type conversion")
        
        # Test various input types
        test_values = [
            42,  # int
            3.14,  # float
            "2.718",  # string
            "  -1.5  ",  # string with whitespace
            "not a number",  # invalid string
            None,  # None
            {"key": "value"},  # dict
        ]
        
        for value in test_values:
            result = robust_float_conversion(value)
            logger.info(f"Converted {type(value).__name__} '{value}' to {result}")
        
        # Demonstrate list conversion
        test_lists = [
            [1, 2, 3],  # normal list
            [1, "2", 3.0],  # mixed types
            [1, 2],  # too short
            [1, 2, 3, 4, 5],  # too long
            "not a list",  # not a list
            None,  # None
        ]
        
        for lst in test_lists:
            result = robust_list_conversion(lst, dimension=3)
            logger.info(f"Converted {type(lst).__name__} '{lst}' to {result}")
        
        # Demonstrate query with various embedding types
        logger.info("Demonstrating queries with various embedding types")
        
        # Valid numpy array
        valid_embedding = np.random.rand(384).astype(np.float32)
        chunks, scores = await client.query_chunks(valid_embedding)
        logger.info(f"Query with valid embedding returned {len(chunks)} results")
        
        # Valid list
        valid_list = valid_embedding.tolist()
        # Convert list to numpy array to ensure type compatibility
        valid_list_array = np.array(valid_list, dtype=np.float32)
        chunks, scores = await client.query_chunks(valid_list_array)
        logger.info(f"Query with valid list returned {len(chunks)} results")
        
        # Mixed type list
        mixed_list = [1, 2.5, "3"] + [0.0] * 381
        chunks, scores = await client.query_chunks(mixed_list)
        logger.info(f"Query with mixed type list returned {len(chunks)} results")
        
        # Wrong dimension
        wrong_dim = np.random.rand(100).astype(np.float32)
        chunks, scores = await client.query_chunks(wrong_dim)
        logger.info(f"Query with wrong dimension returned {len(chunks)} results")
        
        logger.info("Error handling demonstration completed successfully")
        
    except Exception as e:
        logger.error(f"Unexpected error in demonstration: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
    finally:
        # Clean up
        if client:
            await client.shutdown()
        
        # Remove the temporary database file
        if os.path.exists(db_path):
            os.remove(db_path)

"""
## Running the Demo

To run this demonstration, execute the following code:
"""

if __name__ == "__main__":
    asyncio.run(run_error_handling_demo())

"""
## Conclusion

This notebook demonstrated best practices for error handling in Llama Stack:

1. **Robust Type Conversion**: Safely handle unexpected input types
2. **Graceful Failure and Recovery**: Implement retry logic and fallback mechanisms
3. **Comprehensive Logging**: Track operations and diagnose issues with detailed logging
4. **Practical Implementation**: Combine these techniques in a robust client

By following these practices, you can build more reliable and maintainable research code
that gracefully handles unexpected situations and provides clear diagnostics when issues occur.
"""

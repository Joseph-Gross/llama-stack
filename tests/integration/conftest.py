"""Configuration for integration tests."""

import os
import pytest
from unittest.mock import MagicMock, patch

from llama_stack.distribution.server.server import app
from llama_stack.distribution.stack import LlamaStack
from llama_stack.apis.inference.inference import InferenceProtocol
from llama_stack.apis.safety.safety import SafetyProtocol
from llama_stack.apis.vector_io.vector_io import VectorIOProtocol


class MockInferenceProvider(InferenceProtocol):
    """Mock implementation of InferenceProtocol for testing."""
    
    async def generate(self, prompt, max_tokens=100, **kwargs):
        """Mock generate method."""
        return {"text": f"Generated text for: {prompt[:10]}..."}
    
    async def chat(self, messages, max_tokens=100, **kwargs):
        """Mock chat method."""
        return {"message": {"role": "assistant", "content": "Hello! How can I help you?"}}
    
    async def embeddings(self, input, **kwargs):
        """Mock embeddings method."""
        return {"embeddings": [[0.1, 0.2, 0.3] for _ in range(len(input))]}
    
    async def shutdown(self):
        """Mock shutdown method."""
        pass


class MockSafetyProvider(SafetyProtocol):
    """Mock implementation of SafetyProtocol for testing."""
    
    async def check(self, text, **kwargs):
        """Mock check method."""
        return {"results": [{"category": "harmful", "flagged": False, "score": 0.01}]}
    
    async def shutdown(self):
        """Mock shutdown method."""
        pass


class MockVectorIOProvider(VectorIOProtocol):
    """Mock implementation of VectorIOProtocol for testing."""
    
    async def store(self, documents, **kwargs):
        """Mock store method."""
        return {"document_ids": [doc["id"] for doc in documents]}
    
    async def retrieve(self, query, top_k=3, **kwargs):
        """Mock retrieve method."""
        return {"documents": [{"id": "doc1", "text": "Test document", "score": 0.95}]}
    
    async def shutdown(self):
        """Mock shutdown method."""
        pass


@pytest.fixture(autouse=True)
def mock_llama_stack():
    """Mock LlamaStack for testing."""
    with patch.object(app, "__llama_stack_impls__", {
        "inference": MockInferenceProvider(),
        "safety": MockSafetyProvider(),
        "vector_io": MockVectorIOProvider(),
    }):
        yield

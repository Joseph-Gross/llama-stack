"""Integration tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient

from llama_stack.distribution.server.server import app
from llama_stack.apis.version import LLAMA_STACK_API_VERSION


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


def test_inference_generate_endpoint(client):
    """Test the inference generate endpoint."""
    response = client.post(
        f"/{LLAMA_STACK_API_VERSION}/inference/generate",
        json={
            "prompt": "Hello, world!",
            "max_tokens": 10,
        },
    )
    assert response.status_code == 200
    assert "text" in response.json()


def test_inference_chat_endpoint(client):
    """Test the inference chat endpoint."""
    response = client.post(
        f"/{LLAMA_STACK_API_VERSION}/inference/chat",
        json={
            "messages": [
                {"role": "user", "content": "Hello, how are you?"}
            ],
            "max_tokens": 10,
        },
    )
    assert response.status_code == 200
    assert "message" in response.json()


def test_inference_embeddings_endpoint(client):
    """Test the inference embeddings endpoint."""
    response = client.post(
        f"/{LLAMA_STACK_API_VERSION}/inference/embeddings",
        json={
            "input": ["Hello, world!"],
        },
    )
    assert response.status_code == 200
    assert "embeddings" in response.json()


def test_error_handling_invalid_parameters(client):
    """Test error handling for invalid parameters."""
    response = client.post(
        f"/{LLAMA_STACK_API_VERSION}/inference/generate",
        json={
            "prompt": "Hello, world!",
            "max_tokens": -1,  # Invalid value
        },
    )
    assert response.status_code == 400
    assert "error" in response.json()


def test_error_handling_missing_parameters(client):
    """Test error handling for missing required parameters."""
    response = client.post(
        f"/{LLAMA_STACK_API_VERSION}/inference/generate",
        json={
            # Missing prompt
            "max_tokens": 10,
        },
    )
    assert response.status_code == 400
    assert "error" in response.json()


def test_error_handling_invalid_endpoint(client):
    """Test error handling for invalid endpoint."""
    response = client.post(
        f"/{LLAMA_STACK_API_VERSION}/inference/nonexistent_endpoint",
        json={
            "prompt": "Hello, world!",
            "max_tokens": 10,
        },
    )
    assert response.status_code == 404
    assert "error" in response.json() or "detail" in response.json()


def test_safety_check_endpoint(client):
    """Test the safety check endpoint."""
    response = client.post(
        f"/{LLAMA_STACK_API_VERSION}/safety/check",
        json={
            "text": "This is a safe text.",
        },
    )
    assert response.status_code == 200
    assert "results" in response.json()


def test_vector_io_store_endpoint(client):
    """Test the vector IO store endpoint."""
    response = client.post(
        f"/{LLAMA_STACK_API_VERSION}/vector_io/store",
        json={
            "documents": [
                {"id": "doc1", "text": "This is a test document."},
            ],
        },
    )
    assert response.status_code == 200
    assert "document_ids" in response.json()


def test_vector_io_retrieve_endpoint(client):
    """Test the vector IO retrieve endpoint."""
    response = client.post(
        f"/{LLAMA_STACK_API_VERSION}/vector_io/retrieve",
        json={
            "query": "test document",
            "top_k": 1,
        },
    )
    assert response.status_code == 200
    assert "documents" in response.json()

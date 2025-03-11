# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.

import pytest
import requests
from fastapi.testclient import TestClient
from llama_stack.distribution.server.rate_limit import RateLimitMiddleware
from llama_stack.distribution.server.middleware import RequestValidationMiddleware
from llama_stack.distribution.server.security_headers import SecurityHeadersMiddleware
from llama_stack.distribution.security.api_keys import SecureApiKeyHandler
from fastapi import FastAPI

@pytest.fixture
def test_app():
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware, limit=5, window=10)
    app.add_middleware(SecurityHeadersMiddleware)
    return app

@pytest.fixture
def client(test_app):
    return TestClient(test_app)

def test_rate_limiting(client):
    """Test that rate limiting works correctly."""
    # Make requests up to the limit
    for _ in range(5):
        response = client.get("/")
        assert response.status_code != 429
        
    # Next request should be rate limited
    response = client.get("/")
    assert response.status_code == 429
    assert "Retry-After" in response.headers

def test_security_headers(client):
    """Test that security headers are added to responses."""
    response = client.get("/")
    
    # Check security headers
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("X-XSS-Protection") == "1; mode=block"
    assert "Strict-Transport-Security" in response.headers
    assert "Content-Security-Policy" in response.headers
    assert "Referrer-Policy" in response.headers

def test_api_key_handler():
    """Test that API key handler works correctly."""
    handler = SecureApiKeyHandler("test-secret")
    
    # Generate a key
    api_key = handler.generate_api_key("test-user")
    
    # Validate the key
    is_valid, user_id = handler.validate_api_key(api_key)
    assert is_valid
    assert user_id == "test-user"
    
    # Test invalid key
    is_valid, user_id = handler.validate_api_key("invalid-key")
    assert not is_valid
    assert user_id is None

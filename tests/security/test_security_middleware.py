# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.

import json
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from llama_stack.distribution.server.server import (
    CORSMiddleware,
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
)


class TestSecurityMiddleware:
    def test_security_headers(self):
        """Test that security headers are added to responses."""
        app = FastAPI()
        app.add_middleware(SecurityHeadersMiddleware)
        
        @app.get("/test")
        def test_endpoint():
            return {"message": "test"}
                
        client = TestClient(app)
        response = client.get("/test")
        
        assert response.headers.get("x-content-type-options") == "nosniff"
        assert response.headers.get("x-frame-options") == "DENY"
        assert "content-security-policy" in response.headers
        assert "strict-transport-security" in response.headers
        assert response.headers.get("x-xss-protection") == "1; mode=block"
        assert response.headers.get("referrer-policy") == "no-referrer"
        assert response.headers.get("cache-control") == "no-store"
        assert response.headers.get("pragma") == "no-cache"

    def test_cors_middleware(self):
        """Test CORS middleware functionality."""
        app = FastAPI()
        app.add_middleware(CORSMiddleware)
        
        @app.get("/test")
        def test_endpoint():
            return {"message": "test"}
                
        client = TestClient(app)
        
        # Test preflight request
        response = client.options(
            "/test",
            headers={"Origin": "http://example.com", "Access-Control-Request-Method": "GET"},
        )
        assert response.status_code == 200
        assert response.headers.get("access-control-allow-origin") == "*"
        assert "GET" in response.headers.get("access-control-allow-methods")
        
        # Test actual request
        response = client.get("/test", headers={"Origin": "http://example.com"})
        assert response.status_code == 200
        assert response.headers.get("access-control-allow-origin") == "*"

    def test_rate_limit_middleware(self):
        """Test rate limiting functionality."""
        app = FastAPI()
        # Set a low rate limit for testing
        middleware = RateLimitMiddleware(app)
        middleware.rate_limit = 5
        app.add_middleware(lambda app: middleware)
        
        @app.get("/test")
        def test_endpoint():
            return {"message": "test"}
                
        client = TestClient(app)
        
        # Make requests up to the limit
        for _ in range(5):
            response = client.get("/test")
            assert response.status_code == 200
                
        # This request should be rate limited
        response = client.get("/test")
        assert response.status_code == 429
        assert "rate limit exceeded" in response.json()["error"]["message"].lower()

# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.

import time
from typing import Dict, List, Optional, Tuple
import logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

log = logging.getLogger(__name__)

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware for rate limiting requests to prevent DoS attacks.
    Uses a sliding window algorithm to track requests.
    """
    
    def __init__(
        self, 
        app, 
        limit: int = 100,
        window: int = 60,
        by_ip: bool = True
    ):
        super().__init__(app)
        self.limit = limit  # Max requests per window
        self.window = window  # Window size in seconds
        self.by_ip = by_ip  # Whether to track by IP
        self.requests: Dict[str, List[float]] = {}
        
    async def dispatch(self, request: Request, call_next):
        # Get client identifier (IP or other)
        client_id = self._get_client_id(request)
        
        # Check if client is rate limited
        limited, retry_after = self._is_rate_limited(client_id)
        
        if limited:
            # Return 429 Too Many Requests
            response = Response(
                content="Rate limit exceeded. Please try again later.",
                status_code=429
            )
            response.headers["Retry-After"] = str(retry_after)
            return response
            
        # Track this request
        self._track_request(client_id)
        
        # Continue with the request
        return await call_next(request)
        
    def _get_client_id(self, request: Request) -> str:
        """Get a unique identifier for the client."""
        if self.by_ip:
            return request.client.host
        return request.headers.get("X-API-Key", request.client.host)
        
    def _is_rate_limited(self, client_id: str) -> Tuple[bool, int]:
        """Check if client is rate limited and return retry time if so."""
        now = time.time()
        
        # If client not seen before, not rate limited
        if client_id not in self.requests:
            return False, 0
            
        # Clean up old requests outside the window
        self.requests[client_id] = [
            t for t in self.requests[client_id] 
            if now - t < self.window
        ]
        
        # Check if too many requests in the window
        if len(self.requests[client_id]) >= self.limit:
            # Calculate retry time (oldest request + window)
            oldest = min(self.requests[client_id])
            retry_after = int(oldest + self.window - now)
            return True, max(1, retry_after)
            
        return False, 0
        
    def _track_request(self, client_id: str):
        """Track a new request for the client."""
        now = time.time()
        
        if client_id not in self.requests:
            self.requests[client_id] = []
            
        self.requests[client_id].append(now)

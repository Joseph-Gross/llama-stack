# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.

import logging
from typing import Any, Dict, Optional

from fastapi import Request
from pydantic import BaseModel, ValidationError

log = logging.getLogger(__name__)

class RequestValidationMiddleware:
    """Middleware for validating incoming requests against schema models."""
    
    def __init__(self, app, validation_models: Dict[str, BaseModel] = None):
        self.app = app
        self.validation_models = validation_models or {}
        
    async def __call__(self, request: Request, call_next):
        path = request.url.path
        
        # Skip validation for paths without defined models
        if path not in self.validation_models:
            return await call_next(request)
            
        try:
            # Get request body
            body = await request.json()
            
            # Validate against model
            model = self.validation_models[path]
            model.model_validate(body)
            
            # Continue with validated request
            return await call_next(request)
        except ValidationError as e:
            log.warning(f"Request validation failed: {e}")
            return {
                "status_code": 400,
                "detail": "Invalid request data",
                "errors": e.errors()
            }
        except Exception as e:
            log.error(f"Error in request validation: {e}")
            return await call_next(request)

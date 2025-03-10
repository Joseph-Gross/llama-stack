# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.

import json
import logging
import traceback
from typing import Callable, Dict, Optional

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from llama_stack.common.exceptions import (
    ConfigurationException,
    ErrorSeverity,
    LlamaStackException,
    ProviderException,
    ResourceNotFoundException,
    SafetyException,
    ValidationException,
)
from llama_stack.common.logging import get_logger
from llama_stack.common.context import get_current_context

logger = get_logger(__name__)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for standardized error handling across the API."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and handle any exceptions.
        
        Args:
            request: The incoming request
            call_next: The next middleware or route handler
            
        Returns:
            The response
        """
        try:
            return await call_next(request)
        except Exception as exc:
            return self._handle_exception(exc, request)
    
    def _handle_exception(self, exc: Exception, request: Request) -> JSONResponse:
        """
        Handle exceptions and return appropriate responses.
        
        Args:
            exc: The exception to handle
            request: The request that caused the exception
            
        Returns:
            Standardized JSON response with error details
        """
        # Get request context for logging
        context = {
            "path": request.url.path,
            "method": request.method,
            "client": str(request.client),
            **get_current_context()
        }
        
        if isinstance(exc, LlamaStackException):
            # Handle known Llama Stack exceptions
            status_code = self._get_status_code_for_exception(exc)
            # Access attributes that are specific to LlamaStackException
            error_response = {
                "error": {
                    "code": exc.error_code,
                    "message": exc.message,
                    "details": exc.details
                }
            }
            
            # Log the exception with appropriate level
            self._log_exception(exc, context)
            
            return JSONResponse(
                status_code=status_code,
                content=error_response
            )
        else:
            # Handle unexpected exceptions
            logger.error(
                f"Unexpected error: {str(exc)}",
                extra={"context": context},
                exc_info=True
            )
            
            return JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "code": "INTERNAL_SERVER_ERROR",
                        "message": "An unexpected error occurred",
                        "details": {
                            "type": exc.__class__.__name__,
                            "message": str(exc)
                        }
                    }
                }
            )
    
    def _get_status_code_for_exception(self, exc: LlamaStackException) -> int:
        """
        Map exception types to HTTP status codes.
        
        Args:
            exc: The exception to map
            
        Returns:
            The appropriate HTTP status code
        """
        exception_status_map = {
            ValidationException: 400,
            ProviderException: 502,
            SafetyException: 403,
            ResourceNotFoundException: 404,
            ConfigurationException: 500
        }
        
        for exc_type, status_code in exception_status_map.items():
            if isinstance(exc, exc_type):
                return status_code
        
        return 500
    
    def _log_exception(self, exc: LlamaStackException, context: Dict) -> None:
        """
        Log exception with appropriate level based on severity.
        
        Args:
            exc: The exception to log
            context: Additional context for the log
        """
        log_level_map = {
            ErrorSeverity.DEBUG: logging.DEBUG,
            ErrorSeverity.INFO: logging.INFO,
            ErrorSeverity.WARNING: logging.WARNING,
            ErrorSeverity.ERROR: logging.ERROR,
            ErrorSeverity.CRITICAL: logging.CRITICAL
        }
        
        log_level = log_level_map.get(exc.severity, logging.ERROR)
        
        # Merge exception details with context
        log_context = {**context, **exc.details}
        
        logger.log(
            log_level,
            f"{exc.__class__.__name__}: {exc.message}",
            extra={"context": log_context},
            exc_info=True if log_level >= logging.ERROR else False
        )


def add_error_handling(app: FastAPI) -> None:
    """
    Add error handling middleware to FastAPI app.
    
    Args:
        app: The FastAPI application
    """
    app.add_middleware(ErrorHandlingMiddleware)

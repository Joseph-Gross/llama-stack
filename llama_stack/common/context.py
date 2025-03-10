# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.

import contextvars
import uuid
from typing import Any, Dict, Optional

# Context variables for tracking request context
request_id_var = contextvars.ContextVar("request_id", default="")
trace_id_var = contextvars.ContextVar("trace_id", default="")
context_data_var = contextvars.ContextVar("context_data", default={})


def get_request_id() -> str:
    """
    Get the current request ID from context.
    
    Returns:
        The current request ID or empty string if not set
    """
    return request_id_var.get()


def set_request_id(request_id: Optional[str] = None) -> None:
    """
    Set the current request ID in context.
    
    Args:
        request_id: The request ID to set, or generate a new one if None
    """
    if request_id is None:
        request_id = str(uuid.uuid4())
    
    # Set the context variable with the request ID
    request_id_var.set(request_id)


def get_trace_id() -> str:
    """
    Get the current trace ID from context.
    
    Returns:
        The current trace ID or empty string if not set
    """
    return trace_id_var.get()


def set_trace_id(trace_id: Optional[str] = None) -> None:
    """
    Set the current trace ID in context.
    
    Args:
        trace_id: The trace ID to set, or generate a new one if None
    """
    if trace_id is None:
        trace_id = str(uuid.uuid4())
    
    # Set the context variable with the trace ID
    trace_id_var.set(trace_id)


def get_context_data() -> Dict[str, Any]:
    """
    Get the current context data.
    
    Returns:
        The current context data dictionary
    """
    return context_data_var.get().copy()


def set_context_data(data: Dict[str, Any]) -> None:
    """
    Set the current context data.
    
    Args:
        data: The context data to set
    """
    context_data_var.set(data)


def update_context_data(data: Dict[str, Any]) -> None:
    """
    Update the current context data with new values.
    
    Args:
        data: The context data to update with
    """
    current_data = get_context_data()
    current_data.update(data)
    set_context_data(current_data)


def get_current_context() -> Dict[str, Any]:
    """
    Get the complete current context including request ID, trace ID, and context data.
    
    Returns:
        Dictionary with all context information
    """
    context = get_context_data()
    
    request_id = get_request_id()
    if request_id:
        context["request_id"] = request_id
    
    trace_id = get_trace_id()
    if trace_id:
        context["trace_id"] = trace_id
    
    return context


class ContextManager:
    """Context manager for setting and clearing request context."""
    
    def __init__(
        self,
        request_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        context_data: Optional[Dict[str, Any]] = None
    ):
        self.request_id = request_id
        self.trace_id = trace_id
        self.context_data = context_data or {}
        
        # Store previous context
        self.prev_request_id = None
        self.prev_trace_id = None
        self.prev_context_data = None
    
    def __enter__(self):
        # Store previous context
        self.prev_request_id = get_request_id()
        self.prev_trace_id = get_trace_id()
        self.prev_context_data = get_context_data()
        
        # Set new context
        set_request_id(self.request_id)
        set_trace_id(self.trace_id)
        set_context_data(self.context_data)
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore previous context
        if self.prev_request_id is not None:
            # Restore previous request ID
            request_id_var.set(self.prev_request_id)
        
        if self.prev_trace_id is not None:
            # Restore previous trace ID
            trace_id_var.set(self.prev_trace_id)
        
        if self.prev_context_data is not None:
            # Restore previous context data
            context_data_var.set(self.prev_context_data)

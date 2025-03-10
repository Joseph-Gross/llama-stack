# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.

from enum import Enum
from typing import Any, Dict, Optional, Type


class ErrorSeverity(Enum):
    """Severity levels for errors to enable appropriate handling and reporting."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class LlamaStackException(Exception):
    """Base exception class for all Llama Stack exceptions with enhanced context."""
    
    def __init__(
        self, 
        message: str, 
        error_code: Optional[str] = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        self.message = message
        self.error_code = error_code or "UNKNOWN_ERROR"
        self.severity = severity
        self.details = details or {}
        self.cause = cause
        
        # Format the error message with context
        formatted_message = f"[{self.error_code}] {self.message}"
        if self.details:
            formatted_message += f" Details: {self.details}"
        
        super().__init__(formatted_message)


class ValidationException(LlamaStackException):
    """Exception raised for input validation errors."""
    
    def __init__(
        self, 
        message: str, 
        field_name: Optional[str] = None,
        expected_type: Optional[Type] = None,
        received_value: Any = None,
        **kwargs
    ):
        details = kwargs.pop("details", {})
        details.update({
            "field_name": field_name,
            "expected_type": str(expected_type) if expected_type else None,
            "received_value": str(received_value) if received_value is not None else None
        })
        
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            severity=ErrorSeverity.WARNING,
            details=details,
            **kwargs
        )


class ProviderException(LlamaStackException):
    """Exception raised for provider-related errors."""
    
    def __init__(
        self, 
        message: str, 
        provider_name: Optional[str] = None,
        operation: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.pop("details", {})
        details.update({
            "provider_name": provider_name,
            "operation": operation
        })
        
        super().__init__(
            message=message,
            error_code="PROVIDER_ERROR",
            severity=ErrorSeverity.ERROR,
            details=details,
            **kwargs
        )


class SafetyException(LlamaStackException):
    """Exception raised for safety violations."""
    
    def __init__(
        self, 
        message: str, 
        violation_type: Optional[str] = None,
        content: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.pop("details", {})
        details.update({
            "violation_type": violation_type,
            "content": content
        })
        
        super().__init__(
            message=message,
            error_code="SAFETY_VIOLATION",
            severity=ErrorSeverity.ERROR,
            details=details,
            **kwargs
        )


class TypeValidationException(ValidationException):
    """Exception raised specifically for type validation errors."""
    
    def __init__(
        self,
        message: str,
        param_name: str,
        expected_type: Type,
        received_type: Type,
        **kwargs
    ):
        super().__init__(
            message=message,
            field_name=param_name,
            expected_type=expected_type,
            received_value=f"value of type {received_type.__name__}",
            **kwargs
        )


class ConfigurationException(LlamaStackException):
    """Exception raised for configuration errors."""
    
    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.pop("details", {})
        if config_key:
            details["config_key"] = config_key
            
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            severity=ErrorSeverity.ERROR,
            details=details,
            **kwargs
        )


class ResourceNotFoundException(LlamaStackException):
    """Exception raised when a requested resource is not found."""
    
    def __init__(
        self,
        message: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.pop("details", {})
        details.update({
            "resource_type": resource_type,
            "resource_id": resource_id
        })
        
        super().__init__(
            message=message,
            error_code="RESOURCE_NOT_FOUND",
            severity=ErrorSeverity.WARNING,
            details=details,
            **kwargs
        )

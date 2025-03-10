# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.

import functools
import inspect
from typing import Any, Callable, Dict, List, Optional, Type, Union, get_type_hints

from llama_stack.common.exceptions import TypeValidationException, ValidationException
from llama_stack.common.logging import get_logger

logger = get_logger(__name__)


def validate_types(func: Callable) -> Callable:
    """
    Decorator that validates function arguments against their type annotations.
    
    Args:
        func: The function to validate arguments for
        
    Returns:
        Decorated function with type validation
        
    Raises:
        TypeValidationException: If an argument doesn't match its type annotation
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        sig = inspect.signature(func)
        type_hints = get_type_hints(func)
        
        # Get bound arguments
        bound_args = sig.bind(*args, **kwargs)
        bound_args.apply_defaults()
        
        # Validate each argument
        for param_name, param_value in bound_args.arguments.items():
            # Skip return type annotation
            if param_name == "return":
                continue
                
            if param_name in type_hints:
                expected_type = type_hints[param_name]
                
                # Perform type validation
                if not _is_valid_type(param_value, expected_type):
                    raise TypeValidationException(
                        message=f"Invalid type for parameter '{param_name}'",
                        param_name=param_name,
                        expected_type=expected_type,
                        received_type=type(param_value)
                    )
        
        return func(*args, **kwargs)
    
    return wrapper


def _is_valid_type(value: Any, expected_type: Type) -> bool:
    """
    Check if a value matches the expected type.
    
    Args:
        value: The value to check
        expected_type: The expected type
        
    Returns:
        True if the value matches the expected type, False otherwise
    """
    # Handle None for Optional types
    if value is None:
        # Check if this is an Optional type
        origin = getattr(expected_type, "__origin__", None)
        if origin is Union:
            args = getattr(expected_type, "__args__", ())
            if type(None) in args:
                return True
        return False
    
    # Handle Union types
    origin = getattr(expected_type, "__origin__", None)
    if origin is Union:
        args = getattr(expected_type, "__args__", ())
        return any(_is_valid_type(value, arg) for arg in args)
    
    # Handle List, Dict, etc.
    if origin is list and isinstance(value, list):
        item_type = expected_type.__args__[0]
        return all(_is_valid_type(item, item_type) for item in value)
    
    if origin is dict and isinstance(value, dict):
        key_type, value_type = expected_type.__args__
        return (all(_is_valid_type(k, key_type) for k in value.keys()) and
                all(_is_valid_type(v, value_type) for v in value.values()))
    
    # Handle basic types
    try:
        return isinstance(value, expected_type)
    except TypeError:
        # Fall back to simple type name comparison for complex types
        return type(value).__name__ == getattr(expected_type, "__name__", None)


def validate_input(schema: Dict[str, Type]) -> Callable:
    """
    Decorator that validates input against a schema.
    
    Args:
        schema: Dictionary mapping field names to expected types
        
    Returns:
        Decorator function
        
    Raises:
        ValidationException: If input doesn't match the schema
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Assume first argument is the input data for validation
            if not args:
                raise ValidationException(
                    message="No input data provided for validation"
                )
            
            input_data = args[0]
            
            # Validate against schema
            for field_name, expected_type in schema.items():
                if field_name not in input_data:
                    raise ValidationException(
                        message=f"Missing required field '{field_name}'",
                        field_name=field_name
                    )
                
                field_value = input_data[field_name]
                if not _is_valid_type(field_value, expected_type):
                    raise ValidationException(
                        message=f"Invalid type for field '{field_name}'",
                        field_name=field_name,
                        expected_type=expected_type,
                        received_value=field_value
                    )
            
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator


def validate_required_fields(required_fields: List[str]) -> Callable:
    """
    Decorator that validates that required fields are present in the input.
    
    Args:
        required_fields: List of required field names
        
    Returns:
        Decorator function
        
    Raises:
        ValidationException: If a required field is missing
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Assume first argument is the input data for validation
            if not args:
                raise ValidationException(
                    message="No input data provided for validation"
                )
            
            input_data = args[0]
            
            # Check for required fields
            for field_name in required_fields:
                if field_name not in input_data:
                    raise ValidationException(
                        message=f"Missing required field '{field_name}'",
                        field_name=field_name
                    )
            
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator

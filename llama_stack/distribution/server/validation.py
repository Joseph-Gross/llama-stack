# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.

import logging
import re
from typing import Any, Dict, List, Optional, Pattern, Set

log = logging.getLogger(__name__)

# Common validation patterns
ALPHANUMERIC_PATTERN: Pattern = re.compile(r'^[a-zA-Z0-9_\-\.]+$')
UUID_PATTERN: Pattern = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')
EMAIL_PATTERN: Pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
URL_PATTERN: Pattern = re.compile(r'^https?://[a-zA-Z0-9][-a-zA-Z0-9.]*\.[a-zA-Z]{2,}(/[-a-zA-Z0-9_%/.~]*)?(\?[a-zA-Z0-9=%&_.-]*)?$')

# Maximum sizes for different input types
MAX_STRING_LENGTH = 10000  # 10KB
MAX_LIST_ITEMS = 1000
MAX_DICT_ITEMS = 1000
MAX_NESTED_DEPTH = 10

class ValidationError(Exception):
    """Exception raised for validation errors."""
    pass

def validate_string(value: str, field_name: str, max_length: int = MAX_STRING_LENGTH, 
                    pattern: Optional[Pattern] = None) -> str:
    """Validate a string value."""
    if not isinstance(value, str):
        raise ValidationError(f"{field_name} must be a string")
    
    if len(value) > max_length:
        raise ValidationError(f"{field_name} exceeds maximum length of {max_length} characters")
    
    if pattern and not pattern.match(value):
        raise ValidationError(f"{field_name} does not match required pattern")
    
    return value

def validate_list(value: List[Any], field_name: str, max_items: int = MAX_LIST_ITEMS) -> List[Any]:
    """Validate a list value."""
    if not isinstance(value, list):
        raise ValidationError(f"{field_name} must be a list")
    
    if len(value) > max_items:
        raise ValidationError(f"{field_name} exceeds maximum of {max_items} items")
    
    return value

def validate_dict(value: Dict[str, Any], field_name: str, max_items: int = MAX_DICT_ITEMS,
                 required_keys: Optional[Set[str]] = None, 
                 allowed_keys: Optional[Set[str]] = None) -> Dict[str, Any]:
    """Validate a dictionary value."""
    if not isinstance(value, dict):
        raise ValidationError(f"{field_name} must be a dictionary")
    
    if len(value) > max_items:
        raise ValidationError(f"{field_name} exceeds maximum of {max_items} items")
    
    if required_keys:
        missing_keys = required_keys - set(value.keys())
        if missing_keys:
            raise ValidationError(f"{field_name} is missing required keys: {', '.join(missing_keys)}")
    
    if allowed_keys:
        invalid_keys = set(value.keys()) - allowed_keys
        if invalid_keys:
            raise ValidationError(f"{field_name} contains invalid keys: {', '.join(invalid_keys)}")
    
    return value

def validate_nested_structure(value: Any, field_name: str, current_depth: int = 0) -> Any:
    """Recursively validate a nested structure to prevent DoS attacks."""
    if current_depth > MAX_NESTED_DEPTH:
        raise ValidationError(f"{field_name} exceeds maximum nesting depth of {MAX_NESTED_DEPTH}")
    
    if isinstance(value, dict):
        return {k: validate_nested_structure(v, f"{field_name}.{k}", current_depth + 1) 
                for k, v in value.items()}
    elif isinstance(value, list):
        return [validate_nested_structure(item, f"{field_name}[{i}]", current_depth + 1) 
                for i, item in enumerate(value)]
    else:
        return value

class RequestValidator:
    """Utility class for validating request data."""
    
    @staticmethod
    def validate_request_data(data: Dict[str, Any], endpoint_name: str) -> Dict[str, Any]:
        """Validate request data based on the endpoint."""
        try:
            # Validate overall structure
            validate_dict(data, "request_data")
            
            # Validate nested structure to prevent DoS
            data = validate_nested_structure(data, "request_data")
            
            # Endpoint-specific validation could be added here
            if "model_id" in data:
                data["model_id"] = validate_string(data["model_id"], "model_id", pattern=ALPHANUMERIC_PATTERN)
                
            if "prompt" in data:
                data["prompt"] = validate_string(data["prompt"], "prompt")
                
            if "messages" in data:
                data["messages"] = validate_list(data["messages"], "messages")
                
            if "user_id" in data:
                data["user_id"] = validate_string(data["user_id"], "user_id", pattern=ALPHANUMERIC_PATTERN)
                
            return data
            
        except ValidationError as e:
            log.warning(f"Validation error for {endpoint_name}: {str(e)}")
            raise

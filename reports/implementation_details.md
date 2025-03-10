# Implementation Details: Code Governance Improvements

This document provides technical details about the code governance improvements implemented in the Llama Stack codebase.

## 1. Exception Handling Framework

### Core Components

- **Base Exception Class**: `LlamaStackException` in `llama_stack/common/exceptions.py`
- **Error Severity Enum**: `ErrorSeverity` with DEBUG, INFO, WARNING, ERROR, CRITICAL levels
- **Specialized Exception Types**: Hierarchy of exception types for different error categories

### Implementation Details

The exception framework provides:

- **Standardized Error Attributes**:
  - `error_code`: Unique identifier for the error
  - `message`: Human-readable error message
  - `details`: Additional context about the error
  - `severity`: Error severity level

- **Context Preservation**:
  - Captures and preserves error context
  - Maintains stack traces
  - Supports structured error details

- **Integration with Logging**:
  - Severity-based logging
  - Contextual error information in logs

### Usage Example

```python
try:
    # Operation that might fail
    result = process_data(input_data)
except ValidationException as e:
    # Handle validation error
    logger.warning(f"Validation error: {e.message}", extra={"context": e.details})
    # Return appropriate response
```

## 2. Logging Framework

### Core Components

- **Logger Factory**: `get_logger` function in `llama_stack/common/logging.py`
- **JSON Formatter**: Custom formatter for structured JSON logs
- **Context Integration**: Integration with request context

### Implementation Details

The logging framework provides:

- **Structured Logging**:
  - JSON-formatted logs for machine parsing
  - Consistent log format across the application

- **Contextual Information**:
  - Request ID and trace ID in logs
  - Additional context data in log records

- **Configuration Options**:
  - Log level configuration
  - Output format configuration
  - Handler configuration

### Usage Example

```python
from llama_stack.common.logging import get_logger

logger = get_logger(__name__)

def process_request(request_data):
    logger.info("Processing request", extra={"request_data": request_data})
    # Process request
    logger.debug("Request processing complete")
```

## 3. Context Management

### Core Components

- **Context Variables**: Context variables for request ID, trace ID, and context data
- **Context Manager**: `ContextManager` class for managing request context

### Implementation Details

The context management system provides:

- **Request Context Tracking**:
  - Unique request ID generation and tracking
  - Trace ID for distributed tracing
  - Additional context data storage

- **Context Propagation**:
  - Context preservation across async boundaries
  - Context restoration after operations

- **Integration Points**:
  - Middleware integration for HTTP requests
  - Integration with logging system
  - Integration with error handling

### Usage Example

```python
from llama_stack.common.context import ContextManager, get_current_context

async def process_request(request_data):
    with ContextManager(request_id="req-123", context_data={"user": "user-456"}):
        # All operations in this context will have access to the context data
        context = get_current_context()
        # Process request with context
```

## 4. Type Validation System

### Core Components

- **Type Validation Decorators**: Decorators in `llama_stack/common/validation.py`
- **Type Checking Functions**: Functions for validating types at runtime

### Implementation Details

The type validation system provides:

- **Function Argument Validation**:
  - Runtime type checking for function arguments
  - Support for complex types (Optional, List, Dict, Union)
  - Detailed error messages for type mismatches

- **Schema Validation**:
  - Validation against schema definitions
  - Required field validation
  - Type validation for fields

- **Error Handling**:
  - Specialized exceptions for validation errors
  - Context-rich error messages
  - Integration with the exception framework

### Usage Example

```python
from llama_stack.common.validation import validate_types
from typing import Dict, List, Optional

@validate_types
def process_data(data: Dict[str, Any], options: Optional[List[str]] = None) -> Dict[str, Any]:
    # Function implementation
    # Types will be validated at runtime
    return processed_data
```

## 5. Error Handling Middleware

### Core Components

- **Error Handling Middleware**: `ErrorHandlingMiddleware` in `llama_stack/distribution/server/error_middleware.py`
- **Response Formatter**: Functions for formatting error responses

### Implementation Details

The error handling middleware provides:

- **Standardized Error Responses**:
  - Consistent JSON format for error responses
  - Appropriate HTTP status codes
  - Detailed error information

- **Exception Mapping**:
  - Mapping of exception types to HTTP status codes
  - Severity-based logging of exceptions
  - Context preservation in error responses

- **Integration with FastAPI**:
  - Middleware registration with FastAPI
  - Global error handling for all routes
  - Support for async request handling

### Usage Example

```python
from fastapi import FastAPI
from llama_stack.distribution.server.error_middleware import add_error_handling

app = FastAPI()
add_error_handling(app)

@app.get("/api/resource/{id}")
async def get_resource(id: str):
    # If an exception is raised, it will be handled by the middleware
    # and converted to a standardized error response
    return await fetch_resource(id)
```

## 6. Documentation Generation

### Core Components

- **Documentation Generators**: Functions in `llama_stack/common/documentation.py`
- **Markdown Generator**: Function for generating Markdown documentation
- **JSON Generator**: Function for generating JSON documentation

### Implementation Details

The documentation generation system provides:

- **API Documentation**:
  - Class and method documentation
  - Parameter and return type documentation
  - Docstring extraction and formatting

- **Output Formats**:
  - JSON format for machine consumption
  - Markdown format for human consumption

- **Documentation Content**:
  - Method signatures
  - Type annotations
  - Docstrings
  - Default values

### Usage Example

```python
from llama_stack.common.documentation import generate_markdown_documentation

# Generate documentation for a module
generate_markdown_documentation(
    module_path="llama_stack.apis.inference",
    output_dir="docs/api",
    title="Inference API Documentation",
    description="Documentation for the Inference API"
)
```

## 7. Type Safety Improvements

### Core Components

- **Type Annotations**: Improved type annotations throughout the codebase
- **Type Definitions**: Explicit type definitions for complex types

### Implementation Details

The type safety improvements include:

- **Missing Type Definitions**:
  - Defined `Primitive` type in `trace_protocol.py`
  - Added proper type annotations for complex data structures

- **Type Annotation Fixes**:
  - Fixed incorrect default values for typed parameters
  - Added return type annotations
  - Fixed variable type annotations

- **Critical Component Fixes**:
  - Fixed type issues in `safety.py`
  - Improved type safety in `resolver.py`
  - Enhanced type annotations in error handling middleware

### Example Fixes

```python
# Before
def __init__(
    self,
    safety_api: Safety,
    input_shields: List[str] = None,
    output_shields: List[str] = None,
):
    self.safety_api = safety_api
    self.input_shields = input_shields
    self.output_shields = output_shields

# After
def __init__(
    self,
    safety_api: Safety,
    input_shields: Optional[List[str]] = None,
    output_shields: Optional[List[str]] = None,
):
    self.safety_api = safety_api
    self.input_shields = input_shields or []
    self.output_shields = output_shields or []
```

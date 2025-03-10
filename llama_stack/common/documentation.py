# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.

import inspect
import json
import os
from typing import Any, Callable, Dict, List, Optional, Set, Type

from llama_stack.common.logging import get_logger

logger = get_logger(__name__)


def generate_api_documentation(
    module_path: str,
    output_dir: str,
    title: str = "API Documentation",
    description: str = ""
) -> None:
    """
    Generate API documentation for a module.
    
    Args:
        module_path: Path to the module to document
        output_dir: Directory to write documentation to
        title: Documentation title
        description: Documentation description
    """
    import importlib
    
    # Import the module
    try:
        module = importlib.import_module(module_path)
    except ImportError as e:
        logger.error(f"Failed to import module {module_path}: {e}")
        return
    
    # Get all classes and functions
    api_items = _get_api_items(module)
    
    # Generate documentation
    documentation = {
        "title": title,
        "description": description,
        "module": module_path,
        "classes": [],
        "functions": []
    }
    
    # Document classes
    for cls in api_items["classes"]:
        class_doc = _document_class(cls)
        documentation["classes"].append(class_doc)
    
    # Document functions
    for func in api_items["functions"]:
        func_doc = _document_function(func)
        documentation["functions"].append(func_doc)
    
    # Write documentation to file
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"{module_path.replace('.', '_')}.json")
    
    with open(output_file, "w") as f:
        json.dump(documentation, f, indent=2)
    
    logger.info(f"Generated documentation for {module_path} at {output_file}")


def _get_api_items(module: Any) -> Dict[str, List]:
    """
    Extract classes and functions from a module.
    
    Args:
        module: The module to extract items from
        
    Returns:
        Dictionary with classes and functions
    """
    items = {
        "classes": [],
        "functions": []
    }
    
    for name, obj in inspect.getmembers(module):
        # Skip private members
        if name.startswith("_"):
            continue
        
        # Add classes
        if inspect.isclass(obj) and obj.__module__ == module.__name__:
            items["classes"].append(obj)
        
        # Add functions
        if inspect.isfunction(obj) and obj.__module__ == module.__name__:
            items["functions"].append(obj)
    
    return items


def _document_class(cls: Type) -> Dict[str, Any]:
    """
    Generate documentation for a class.
    
    Args:
        cls: The class to document
        
    Returns:
        Documentation for the class
    """
    doc = {
        "name": cls.__name__,
        "docstring": inspect.getdoc(cls) or "",
        "methods": [],
        "attributes": []
    }
    
    # Document methods
    for name, method in inspect.getmembers(cls, predicate=inspect.isfunction):
        # Skip private methods
        if name.startswith("_") and name != "__init__":
            continue
        
        method_doc = _document_function(method)
        doc["methods"].append(method_doc)
    
    # Document attributes
    for name, value in vars(cls).items():
        # Skip private attributes and methods
        if name.startswith("_") or callable(value):
            continue
        
        doc["attributes"].append({
            "name": name,
            "type": type(value).__name__,
            "value": str(value)
        })
    
    return doc


def _document_function(func: Callable) -> Dict[str, Any]:
    """
    Generate documentation for a function.
    
    Args:
        func: The function to document
        
    Returns:
        Documentation for the function
    """
    signature = inspect.signature(func)
    
    doc = {
        "name": func.__name__,
        "docstring": inspect.getdoc(func) or "",
        "parameters": [],
        "return_type": None
    }
    
    # Get type hints
    try:
        type_hints = inspect.get_annotations(func)
    except Exception:
        # Fallback for older Python versions
        type_hints = getattr(func, "__annotations__", {})
    
    # Document parameters
    for name, param in signature.parameters.items():
        param_doc = {
            "name": name,
            "default": str(param.default) if param.default is not inspect.Parameter.empty else None,
            "type": str(type_hints.get(name, "Any")),
            "kind": str(param.kind)
        }
        
        doc["parameters"].append(param_doc)
    
    # Document return type
    if "return" in type_hints:
        doc["return_type"] = str(type_hints["return"])
    
    return doc


def generate_markdown_documentation(
    module_path: str,
    output_dir: str,
    title: str = "API Documentation",
    description: str = ""
) -> None:
    """
    Generate Markdown documentation for a module.
    
    Args:
        module_path: Path to the module to document
        output_dir: Directory to write documentation to
        title: Documentation title
        description: Documentation description
    """
    import importlib
    
    # Import the module
    try:
        module = importlib.import_module(module_path)
    except ImportError as e:
        logger.error(f"Failed to import module {module_path}: {e}")
        return
    
    # Get all classes and functions
    api_items = _get_api_items(module)
    
    # Create markdown content
    markdown = f"# {title}\n\n"
    
    if description:
        markdown += f"{description}\n\n"
    
    markdown += f"Module: `{module_path}`\n\n"
    
    # Document classes
    if api_items["classes"]:
        markdown += "## Classes\n\n"
        
        for cls in api_items["classes"]:
            markdown += _class_to_markdown(cls)
    
    # Document functions
    if api_items["functions"]:
        markdown += "## Functions\n\n"
        
        for func in api_items["functions"]:
            markdown += _function_to_markdown(func)
    
    # Write documentation to file
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"{module_path.replace('.', '_')}.md")
    
    with open(output_file, "w") as f:
        f.write(markdown)
    
    logger.info(f"Generated Markdown documentation for {module_path} at {output_file}")


def _class_to_markdown(cls: Type) -> str:
    """
    Convert a class to Markdown documentation.
    
    Args:
        cls: The class to document
        
    Returns:
        Markdown documentation for the class
    """
    markdown = f"### {cls.__name__}\n\n"
    
    docstring = inspect.getdoc(cls) or ""
    if docstring:
        markdown += f"{docstring}\n\n"
    
    # Document methods
    methods = [
        method for name, method in inspect.getmembers(cls, predicate=inspect.isfunction)
        if not (name.startswith("_") and name != "__init__")
    ]
    
    if methods:
        markdown += "#### Methods\n\n"
        
        for method in methods:
            signature = inspect.signature(method)
            markdown += f"##### `{method.__name__}{signature}`\n\n"
            
            method_doc = inspect.getdoc(method) or ""
            if method_doc:
                markdown += f"{method_doc}\n\n"
    
    markdown += "\n"
    return markdown


def _function_to_markdown(func: Callable) -> str:
    """
    Convert a function to Markdown documentation.
    
    Args:
        func: The function to document
        
    Returns:
        Markdown documentation for the function
    """
    signature = inspect.signature(func)
    markdown = f"### `{func.__name__}{signature}`\n\n"
    
    docstring = inspect.getdoc(func) or ""
    if docstring:
        markdown += f"{docstring}\n\n"
    
    markdown += "\n"
    return markdown

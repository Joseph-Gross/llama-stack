# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.

import json
import logging
import os
import sys
import traceback
from datetime import datetime
from typing import Any, Dict, Optional, Union


class LogLevel:
    """Extended log levels for more granular logging."""
    TRACE = 5
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50


class StructuredLogRecord(logging.LogRecord):
    """Enhanced log record with structured data support."""
    
    def __init__(self, *args, **kwargs):
        self.context = kwargs.pop("context", {})
        super().__init__(*args, **kwargs)


class StructuredLogger(logging.Logger):
    """Logger that supports structured logging with context."""
    
    def makeRecord(self, name, level, fn, lno, msg, args, exc_info, func=None, extra=None, sinfo=None):
        context = {}
        if extra:
            context = extra.pop("context", {}) if isinstance(extra, dict) else {}
        
        record = StructuredLogRecord(
            name, level, fn, lno, msg, args, exc_info, func, sinfo
        )
        record.context = context
        
        if extra:
            for key, value in extra.items():
                setattr(record, key, value)
        
        return record


class JSONFormatter(logging.Formatter):
    """Formatter that outputs JSON formatted logs."""
    
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "line": record.lineno,
        }
        
        # Add context if available
        if hasattr(record, "context") and record.context:
            log_data["context"] = record.context
        
        # Add exception info if available
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        return json.dumps(log_data)


def configure_logging(
    level: Union[int, str] = logging.INFO,
    json_format: bool = False,
    log_file: Optional[str] = None
):
    """
    Configure logging with consistent formatting and handlers.
    
    Args:
        level: The logging level to use
        json_format: Whether to use JSON formatting
        log_file: Optional path to a log file
        
    Returns:
        The configured root logger
    """
    # Register the custom logger class
    logging.setLoggerClass(StructuredLogger)
    
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    
    # Create formatter
    if json_format:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            "%(levelname)s %(asctime)s %(name)s:%(lineno)d: %(message)s"
        )
    
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Add file handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    return root_logger


def get_logger(name: str):
    """
    Get a logger with the specified name.
    
    Args:
        name: The name of the logger
        
    Returns:
        A logger instance
    """
    return logging.getLogger(name)

# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.

import os
import sqlite3
import tempfile
from datetime import datetime

import pytest
from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.trace import SpanContext, SpanKind, StatusCode

from llama_stack.providers.inline.telemetry.meta_reference.sqlite_span_processor import SQLiteSpanProcessor


class TestSQLInjection:
    def test_sql_injection_protection(self):
        """Test that SQL injection attempts are properly handled."""
        # Create a temporary database file
        db_file = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        db_path = db_file.name
        db_file.close()
        
        try:
            # Initialize the processor
            processor = SQLiteSpanProcessor(db_path)
            
            # Create a mock span with SQL injection attempt in trace_id
            mock_span = ReadableSpan(
                name="test_span",
                context=SpanContext(
                    trace_id=0x1234567890ABCDEF,
                    span_id=0x1234567890AB,
                    is_remote=False,
                    trace_flags=1,
                ),
                parent=None,
                resource={},
                attributes={
                    "normal_attribute": "normal value",
                    "service.name": "test-service'; DROP TABLE traces; --",
                },
                events=[],
                links=[],
                kind=SpanKind.INTERNAL,
                start_time=int(datetime.now().timestamp() * 1e9),
                end_time=int(datetime.now().timestamp() * 1e9),
                status=StatusCode.OK,
            )
            
            # Process the span - this should validate inputs and prevent SQL injection
            processor.on_end(mock_span)
            
            # Verify the database integrity
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check if the traces table still exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='traces'")
            assert cursor.fetchone() is not None, "Traces table should still exist"
            
            # Check if the data was properly inserted with sanitized values
            cursor.execute("SELECT * FROM spans WHERE span_id = ?", (format(0x1234567890AB, "016x"),))
            span_data = cursor.fetchone()
            assert span_data is not None, "Span data should be inserted"
            
            # Verify that the malicious service name was truncated/sanitized
            cursor.execute("SELECT service_name FROM traces WHERE trace_id = ?", (format(0x1234567890ABCDEF, "032x"),))
            service_name = cursor.fetchone()[0]
            assert "DROP TABLE" not in service_name, "SQL injection attempt should be sanitized"
            assert len(service_name) <= 100, "Service name should be truncated"
            
        finally:
            # Clean up
            if os.path.exists(db_path):
                os.unlink(db_path)
                
    def test_invalid_trace_id_rejection(self):
        """Test that invalid trace IDs are rejected."""
        # Create a temporary database file
        db_file = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        db_path = db_file.name
        db_file.close()
        
        try:
            # Initialize the processor
            processor = SQLiteSpanProcessor(db_path)
            
            # Create a mock span with invalid trace_id format
            mock_span = ReadableSpan(
                name="test_span",
                context=SpanContext(
                    trace_id=0x1234567890ABCDEF,
                    span_id=0x1234567890AB,
                    is_remote=False,
                    trace_flags=1,
                ),
                parent=None,
                resource={},
                attributes={},
                events=[],
                links=[],
                kind=SpanKind.INTERNAL,
                start_time=int(datetime.now().timestamp() * 1e9),
                end_time=int(datetime.now().timestamp() * 1e9),
                status=StatusCode.OK,
            )
            
            # Create a mock span with invalid trace_id format
            invalid_mock_span = ReadableSpan(
                name="test_span",
                context=SpanContext(
                    trace_id=0x1234567890ABCDEF,
                    span_id=0x1234567890AB,
                    is_remote=False,
                    trace_flags=1,
                ),
                parent=None,
                resource={},
                attributes={
                    "invalid_trace": "invalid'; DROP TABLE traces; --"
                },
                events=[],
                links=[],
                kind=SpanKind.INTERNAL,
                start_time=int(datetime.now().timestamp() * 1e9),
                end_time=int(datetime.now().timestamp() * 1e9),
                status=StatusCode.OK,
            )
            
            # Patch the processor to test invalid trace_id validation
            original_validate = processor._validate_id
            def invalid_validate(*args, **kwargs):
                return "invalid'; DROP TABLE traces; --"
            
            processor._validate_id = invalid_validate
            
            # This should raise a ValueError due to invalid trace_id format
            with pytest.raises(ValueError):
                processor.on_end(invalid_mock_span)
                
            # Restore the original validation function
            processor._validate_id = original_validate
            
        finally:
            # Clean up
            if os.path.exists(db_path):
                os.unlink(db_path)

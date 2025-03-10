# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.

import json
import pytest
import logging

from llama_stack.distribution.request_headers import set_request_provider_data, _THREAD_LOCAL


class TestJSONDeserialization:
    def setup_method(self):
        # Clear thread local storage before each test
        if hasattr(_THREAD_LOCAL, "provider_data_header_value"):
            delattr(_THREAD_LOCAL, "provider_data_header_value")
                
    def test_valid_json(self):
        """Test that valid JSON is properly processed."""
        headers = {
            "x-llamastack-provider-data": '{"key": "value", "number": 42}'
        }
        
        set_request_provider_data(headers)
        
        assert hasattr(_THREAD_LOCAL, "provider_data_header_value")
        assert _THREAD_LOCAL.provider_data_header_value == {"key": "value", "number": 42}
            
    def test_invalid_json(self, caplog):
        """Test that invalid JSON is rejected."""
        with caplog.at_level(logging.ERROR):
            headers = {
                "x-llamastack-provider-data": '{"key": "value", invalid json}'
            }
                
            set_request_provider_data(headers)
                
            assert not hasattr(_THREAD_LOCAL, "provider_data_header_value")
            assert "not encoded as a valid JSON object" in caplog.text
                
    def test_non_object_json(self, caplog):
        """Test that non-object JSON is rejected."""
        with caplog.at_level(logging.ERROR):
            headers = {
                "x-llamastack-provider-data": '"just a string"'
            }
                
            set_request_provider_data(headers)
                
            assert not hasattr(_THREAD_LOCAL, "provider_data_header_value")
            assert "Provider data must be a JSON object" in caplog.text
                
    def test_oversized_json(self, caplog):
        """Test that oversized JSON is rejected."""
        with caplog.at_level(logging.ERROR):
            # Create a large JSON string (>10KB)
            large_data = {"key": "x" * 11000}
            headers = {
                "x-llamastack-provider-data": json.dumps(large_data)
            }
                
            set_request_provider_data(headers)
                
            assert not hasattr(_THREAD_LOCAL, "provider_data_header_value")
            assert "Provider data too large" in caplog.text

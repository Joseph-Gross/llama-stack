# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.

import json
import logging
import threading
from typing import Any, Dict

from .utils.dynamic import instantiate_class_type

log = logging.getLogger(__name__)

_THREAD_LOCAL = threading.local()


class NeedsRequestProviderData:
    def get_request_provider_data(self) -> Any:
        spec = self.__provider_spec__
        assert spec, f"Provider spec not set on {self.__class__}"

        provider_type = spec.provider_type
        validator_class = spec.provider_data_validator
        if not validator_class:
            raise ValueError(f"Provider {provider_type} does not have a validator")

        val = getattr(_THREAD_LOCAL, "provider_data_header_value", None)
        if not val:
            return None

        validator = instantiate_class_type(validator_class)
        try:
            provider_data = validator(**val)
            return provider_data
        except Exception as e:
            log.error(f"Error parsing provider data: {e}")


def set_request_provider_data(headers: Dict[str, str]):
    keys = [
        "X-LlamaStack-Provider-Data",
        "x-llamastack-provider-data",
    ]
    val = None
    for key in keys:
        val = headers.get(key, None)
        if val:
            break

    if not val:
        return

    # Validate input before processing
    if not isinstance(val, str):
        log.error("Provider data is not a string")
        return
        
    # Limit size to prevent DoS attacks
    if len(val) > 10000:  
        log.error(f"Provider data too large: {len(val)} bytes (max 10000)")
        return
        
    try:
        parsed_val = json.loads(val)
        
        # Validate JSON structure
        if not isinstance(parsed_val, dict):
            log.error("Provider data not encoded as a JSON object")
            return
            
        # Check for suspicious patterns
        for k, v in parsed_val.items():
            if not isinstance(k, str):
                log.error(f"Invalid key type in provider data: {type(k)}")
                return
                
            # Prevent potential prototype pollution
            if k.startswith('__') or k in ['constructor', 'prototype']:
                log.error(f"Potentially unsafe key in provider data: {k}")
                return
                
    except json.JSONDecodeError as e:
        log.error(f"Provider data not encoded as a JSON object: {str(e)}")
        return

    _THREAD_LOCAL.provider_data_header_value = parsed_val

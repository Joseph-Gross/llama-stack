# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.

import hashlib
import hmac
import os
import secrets
import time
from typing import Dict, Optional, Tuple

class SecureApiKeyHandler:
    """
    Handles API key validation and generation with secure practices.
    Uses HMAC for key validation to prevent timing attacks.
    """
    
    def __init__(self, secret_key: Optional[str] = None):
        """Initialize with a secret key or generate one."""
        self.secret_key = secret_key or os.environ.get(
            "LLAMA_STACK_API_SECRET", 
            secrets.token_hex(32)
        )
        self._api_keys: Dict[str, Dict] = {}
        
    def generate_api_key(self, user_id: str, expiry: Optional[int] = None) -> str:
        """Generate a new API key for a user."""
        # Create a random token
        token = secrets.token_hex(16)
        
        # Create a signature using HMAC
        signature = self._create_signature(token, user_id)
        
        # Combine token and signature
        api_key = f"{token}.{signature}"
        
        # Store key info
        self._api_keys[api_key] = {
            "user_id": user_id,
            "created": int(time.time()),
            "expiry": expiry
        }
        
        return api_key
        
    def validate_api_key(self, api_key: str) -> Tuple[bool, Optional[str]]:
        """
        Validate an API key and return (is_valid, user_id).
        Uses constant-time comparison to prevent timing attacks.
        """
        try:
            # Split token and signature
            token, signature = api_key.split(".")
            
            # Check if key exists in our store
            if api_key not in self._api_keys:
                return False, None
                
            # Get user_id
            user_id = self._api_keys[api_key]["user_id"]
            
            # Check expiry
            if self._api_keys[api_key].get("expiry"):
                current_time = int(time.time())
                if current_time > self._api_keys[api_key]["expiry"]:
                    return False, None
            
            # Verify signature using constant-time comparison
            expected_signature = self._create_signature(token, user_id)
            if not hmac.compare_digest(signature, expected_signature):
                return False, None
                
            return True, user_id
        except Exception:
            return False, None
            
    def _create_signature(self, token: str, user_id: str) -> str:
        """Create an HMAC signature for the token and user_id."""
        message = f"{token}:{user_id}"
        return hmac.new(
            self.secret_key.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()

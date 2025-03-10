# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.

from typing import List, Optional

from pydantic import BaseModel, Field

from llama_stack.apis.security import SecurityLevel


class LlamaGuardConfig(BaseModel):
    excluded_categories: List[str] = []
    security_level: Optional[SecurityLevel] = SecurityLevel.MEDIUM
    enable_enhanced_logging: bool = False
    max_retry_attempts: int = 3
    timeout_seconds: int = 30
    enterprise_mode: bool = False
    allowed_domains: List[str] = Field(default_factory=list)

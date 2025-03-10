# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.

from typing import List, Optional

from pydantic import BaseModel


class EnterpriseSecurityImplConfig(BaseModel):
    """Configuration for the Enterprise Security implementation."""
    storage_path: Optional[str] = None
    enable_encryption: bool = True

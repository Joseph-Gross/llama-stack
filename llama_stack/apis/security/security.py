# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.

from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

from pydantic import BaseModel, Field

from llama_stack.providers.utils.telemetry.trace_protocol import trace_protocol
from llama_stack.schema_utils import json_schema_type, webmethod


@json_schema_type
class SecurityLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@json_schema_type
class AuditLogType(Enum):
    USER_ACCESS = "user_access"
    ADMIN_ACCESS = "admin_access"
    DATA_ACCESS = "data_access"
    MODEL_INFERENCE = "model_inference"
    CONFIGURATION_CHANGE = "configuration_change"
    SECURITY_EVENT = "security_event"


@json_schema_type
class AuditLogEntry(BaseModel):
    """An entry in the audit log for enterprise security compliance."""
    timestamp: str
    log_type: AuditLogType
    user_id: str
    action: str
    resource_id: Optional[str] = None
    ip_address: Optional[str] = None
    status: str
    details: Dict[str, Any] = Field(default_factory=dict)


@json_schema_type
class EnterpriseSecurityConfig(BaseModel):
    """Configuration for enterprise security features."""
    enable_audit_logging: bool = True
    audit_log_retention_days: int = 90
    security_level: SecurityLevel = SecurityLevel.MEDIUM
    require_encryption: bool = True
    allowed_ip_ranges: List[str] = Field(default_factory=list)
    allowed_domains: List[str] = Field(default_factory=list)
    max_token_lifetime_minutes: int = 60
    enable_rate_limiting: bool = True
    rate_limit_requests_per_minute: int = 100


@json_schema_type
class CreateAuditLogRequest(BaseModel):
    log_entry: AuditLogEntry


@json_schema_type
class QueryAuditLogsRequest(BaseModel):
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    log_types: Optional[List[AuditLogType]] = None
    user_id: Optional[str] = None
    resource_id: Optional[str] = None
    limit: int = 100
    offset: int = 0


@json_schema_type
class QueryAuditLogsResponse(BaseModel):
    logs: List[AuditLogEntry]
    total: int


@json_schema_type
class SecurityConfigResponse(BaseModel):
    config: EnterpriseSecurityConfig


@runtime_checkable
@trace_protocol
class Security(Protocol):
    """Enterprise Security API for managing security configurations and audit logs.
    
    Main functionalities provided by this API:
    - Configure enterprise security settings
    - Create and query audit logs for compliance
    - Manage security levels and encryption requirements
    """

    @webmethod(route="/security/config", method="GET")
    async def get_security_config(self) -> SecurityConfigResponse: ...

    @webmethod(route="/security/config", method="PUT")
    async def update_security_config(self, config: EnterpriseSecurityConfig) -> SecurityConfigResponse: ...

    @webmethod(route="/security/audit-logs", method="POST")
    async def create_audit_log(self, request: CreateAuditLogRequest) -> None: ...

    @webmethod(route="/security/audit-logs", method="GET")
    async def query_audit_logs(self, request: QueryAuditLogsRequest) -> QueryAuditLogsResponse: ...

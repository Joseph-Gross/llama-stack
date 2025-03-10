# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.

from typing import List, Optional

from llama_stack.apis.security import (
    AuditLogEntry,
    CreateAuditLogRequest,
    EnterpriseSecurityConfig,
    QueryAuditLogsRequest,
    QueryAuditLogsResponse,
    Security,
    SecurityConfigResponse,
)
from llama_stack.distribution.datatypes import Api
from llama_stack.distribution.routers.routing_tables import CommonRoutingTableImpl


class SecurityRoutingTable(CommonRoutingTableImpl, Security):
    """Routing table implementation for the Security API."""

    async def get_security_config(self) -> SecurityConfigResponse:
        """Get the current enterprise security configuration."""
        provider = await self.get_provider(Api.security)
        return await provider.get_security_config()

    async def update_security_config(
        self, config: EnterpriseSecurityConfig
    ) -> SecurityConfigResponse:
        """Update the enterprise security configuration."""
        provider = await self.get_provider(Api.security)
        return await provider.update_security_config(config)

    async def create_audit_log(self, request: CreateAuditLogRequest) -> None:
        """Create a new audit log entry."""
        provider = await self.get_provider(Api.security)
        await provider.create_audit_log(request)

    async def query_audit_logs(
        self, request: QueryAuditLogsRequest
    ) -> QueryAuditLogsResponse:
        """Query audit logs based on filter criteria."""
        provider = await self.get_provider(Api.security)
        return await provider.query_audit_logs(request)

# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.

import json
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from llama_stack.apis.security import (
    AuditLogEntry,
    CreateAuditLogRequest,
    EnterpriseSecurityConfig,
    QueryAuditLogsRequest,
    QueryAuditLogsResponse,
    Security,
    SecurityConfigResponse,
    SecurityLevel,
)
from llama_stack.providers.utils.kvstore import KVStore

log = logging.getLogger(__name__)

# Constants for security implementation
SECURITY_CONFIG_KEY = "enterprise_security_config"
AUDIT_LOG_KEY_PREFIX = "audit_log:"


class EnterpriseSecurityImpl(Security):
    """Implementation of the Enterprise Security API."""

    def __init__(self, storage: KVStore) -> None:
        """Initialize the Enterprise Security implementation.
        
        Args:
            storage: KVStore for persisting security configuration and audit logs
        """
        self.storage = storage
        self._config = None

    async def initialize(self) -> None:
        """Initialize the security implementation."""
        # Load or create default security configuration
        config_json = await self.storage.get(SECURITY_CONFIG_KEY)
        if config_json:
            self._config = EnterpriseSecurityConfig.model_validate_json(config_json)
        else:
            self._config = EnterpriseSecurityConfig()
            await self.storage.set(
                SECURITY_CONFIG_KEY, self._config.model_dump_json()
            )
        log.info(f"Enterprise security initialized with level: {self._config.security_level}")

    async def shutdown(self) -> None:
        """Shutdown the security implementation."""
        pass

    async def get_security_config(self) -> SecurityConfigResponse:
        """Get the current enterprise security configuration.
        
        Returns:
            SecurityConfigResponse: The current security configuration
        """
        if not self._config:
            await self.initialize()
        return SecurityConfigResponse(config=self._config)

    async def update_security_config(
        self, config: EnterpriseSecurityConfig
    ) -> SecurityConfigResponse:
        """Update the enterprise security configuration.
        
        Args:
            config: The new security configuration
            
        Returns:
            SecurityConfigResponse: The updated security configuration
        """
        # Create audit log for configuration change
        await self.create_audit_log(
            CreateAuditLogRequest(
                log_entry=AuditLogEntry(
                    timestamp=datetime.now().isoformat(),
                    log_type="configuration_change",
                    user_id="system",  # This should be replaced with actual user ID
                    action="update_security_config",
                    status="success",
                    details={
                        "old_config": self._config.model_dump() if self._config else {},
                        "new_config": config.model_dump(),
                    },
                )
            )
        )
        
        # Update configuration
        self._config = config
        await self.storage.set(SECURITY_CONFIG_KEY, config.model_dump_json())
        log.info(f"Enterprise security configuration updated to level: {config.security_level}")
        
        return SecurityConfigResponse(config=self._config)

    async def create_audit_log(self, request: CreateAuditLogRequest) -> None:
        """Create a new audit log entry.
        
        Args:
            request: The audit log entry to create
        """
        log_entry = request.log_entry
        log_key = f"{AUDIT_LOG_KEY_PREFIX}{int(time.time())}:{log_entry.log_type}"
        
        await self.storage.set(log_key, log_entry.model_dump_json())
        
        # Implement log retention policy
        if self._config and self._config.audit_log_retention_days > 0:
            retention_seconds = self._config.audit_log_retention_days * 86400
            cutoff_time = int(time.time()) - retention_seconds
            
            # In a production implementation, this would use a more efficient
            # method to clean up old logs, possibly with a background task
            # This is a simplified implementation for demonstration
            keys = await self.storage.keys(f"{AUDIT_LOG_KEY_PREFIX}*")
            for key in keys:
                try:
                    timestamp = int(key.split(":")[1])
                    if timestamp < cutoff_time:
                        await self.storage.delete(key)
                except (IndexError, ValueError):
                    log.warning(f"Could not parse timestamp from audit log key: {key}")

    async def query_audit_logs(
        self, request: QueryAuditLogsRequest
    ) -> QueryAuditLogsResponse:
        """Query audit logs based on filter criteria.
        
        Args:
            request: Query parameters for filtering audit logs
            
        Returns:
            QueryAuditLogsResponse: The matching audit logs
        """
        keys = await self.storage.keys(f"{AUDIT_LOG_KEY_PREFIX}*")
        logs: List[AuditLogEntry] = []
        total = 0
        
        for key in keys:
            log_json = await self.storage.get(key)
            if not log_json:
                continue
                
            log_entry = AuditLogEntry.model_validate_json(log_json)
            
            # Apply filters
            if self._should_include_log(log_entry, request):
                total += 1
                if len(logs) < request.limit and total > request.offset:
                    logs.append(log_entry)
        
        return QueryAuditLogsResponse(logs=logs, total=total)
    
    def _should_include_log(
        self, log_entry: AuditLogEntry, request: QueryAuditLogsRequest
    ) -> bool:
        """Determine if a log entry matches the query filters.
        
        Args:
            log_entry: The audit log entry to check
            request: The query parameters
            
        Returns:
            bool: True if the log entry matches the filters, False otherwise
        """
        # Check start time
        if request.start_time and log_entry.timestamp < request.start_time:
            return False
            
        # Check end time
        if request.end_time and log_entry.timestamp > request.end_time:
            return False
            
        # Check log types
        if request.log_types and log_entry.log_type not in request.log_types:
            return False
            
        # Check user ID
        if request.user_id and log_entry.user_id != request.user_id:
            return False
            
        # Check resource ID
        if request.resource_id and log_entry.resource_id != request.resource_id:
            return False
            
        return True

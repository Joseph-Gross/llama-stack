# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.

"""
Enterprise Security Demo for Llama Stack

This example demonstrates how to use the enterprise security features
in Llama Stack to create a secure, auditable AI application.
"""

import asyncio
import datetime
import logging
from typing import List

from llama_stack.apis.agents import AgentConfig, AgentTurnCreateRequest
from llama_stack.apis.inference import UserMessage
from llama_stack.apis.security import (
    AuditLogEntry,
    AuditLogType,
    CreateAuditLogRequest,
    EnterpriseSecurityConfig,
    QueryAuditLogsRequest,
    SecurityLevel,
)
from llama_stack.distribution.library_client import LlamaStackAsLibraryClient
from llama_stack.templates.enterprise_security import ENTERPRISE_SECURITY_TEMPLATE

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_secure_agent(client: LlamaStackAsLibraryClient, user_id: str) -> str:
    """Create a secure agent with enterprise security features."""
    # Log user access
    await client.security.create_audit_log(
        CreateAuditLogRequest(
            log_entry=AuditLogEntry(
                timestamp=datetime.datetime.now().isoformat(),
                log_type=AuditLogType.USER_ACCESS,
                user_id=user_id,
                action="create_agent",
                status="success",
                details={"source_ip": "192.168.1.100"},
            )
        )
    )

    # Create agent with security settings
    agent_id = await client.agents.create_agent(
        AgentConfig(
            instructions="You are a helpful assistant that follows enterprise security guidelines.",
            security_level=SecurityLevel.HIGH,
            allowed_domains=["enterprise.org", "example.com"],
            enable_audit_logging=True,
            input_shields=["llama-guard-3-8b"],
            output_shields=["llama-guard-3-8b"],
        )
    )

    # Log agent creation
    await client.security.create_audit_log(
        CreateAuditLogRequest(
            log_entry=AuditLogEntry(
                timestamp=datetime.datetime.now().isoformat(),
                log_type=AuditLogType.CONFIGURATION_CHANGE,
                user_id=user_id,
                action="agent_created",
                resource_id=agent_id,
                status="success",
                details={"security_level": "high"},
            )
        )
    )

    return agent_id


async def interact_with_agent(
    client: LlamaStackAsLibraryClient, agent_id: str, session_id: str, user_id: str, query: str
) -> None:
    """Interact with the agent and log the interaction."""
    # Log model inference request
    await client.security.create_audit_log(
        CreateAuditLogRequest(
            log_entry=AuditLogEntry(
                timestamp=datetime.datetime.now().isoformat(),
                log_type=AuditLogType.MODEL_INFERENCE,
                user_id=user_id,
                action="agent_query",
                resource_id=agent_id,
                status="started",
                details={"session_id": session_id},
            )
        )
    )

    # Create agent turn
    request = AgentTurnCreateRequest(
        session_id=session_id,
        messages=[UserMessage(content=query)],
        stream=True,
        allow_turn_resume=True,
    )

    # Process agent response
    async for chunk in client.agents.create_turn(agent_id, request):
        # In a real application, you would process the response chunks
        pass

    # Log model inference completion
    await client.security.create_audit_log(
        CreateAuditLogRequest(
            log_entry=AuditLogEntry(
                timestamp=datetime.datetime.now().isoformat(),
                log_type=AuditLogType.MODEL_INFERENCE,
                user_id=user_id,
                action="agent_query",
                resource_id=agent_id,
                status="completed",
                details={"session_id": session_id},
            )
        )
    )


async def query_audit_logs(client: LlamaStackAsLibraryClient, user_id: str) -> List[AuditLogEntry]:
    """Query audit logs for compliance reporting."""
    response = await client.security.query_audit_logs(
        QueryAuditLogsRequest(
            user_id=user_id,
            start_time=(datetime.datetime.now() - datetime.timedelta(days=1)).isoformat(),
            limit=100,
        )
    )
    
    return response.logs


async def update_security_config(client: LlamaStackAsLibraryClient, user_id: str) -> None:
    """Update the enterprise security configuration."""
    # Get current config
    current_config = await client.security.get_security_config()
    
    # Update config
    new_config = EnterpriseSecurityConfig(
        security_level=SecurityLevel.CRITICAL,
        enable_audit_logging=True,
        audit_log_retention_days=180,
        require_encryption=True,
        allowed_domains=["enterprise.org"],
        max_token_lifetime_minutes=30,
        enable_rate_limiting=True,
        rate_limit_requests_per_minute=50,
    )
    
    await client.security.update_security_config(new_config)
    
    # Log configuration change
    await client.security.create_audit_log(
        CreateAuditLogRequest(
            log_entry=AuditLogEntry(
                timestamp=datetime.datetime.now().isoformat(),
                log_type=AuditLogType.CONFIGURATION_CHANGE,
                user_id=user_id,
                action="update_security_config",
                status="success",
                details={
                    "old_security_level": current_config.config.security_level,
                    "new_security_level": new_config.security_level,
                },
            )
        )
    )


async def main():
    """Run the enterprise security demo."""
    logger.info("Starting Enterprise Security Demo")
    
    # Initialize Llama Stack with enterprise security template
    client = LlamaStackAsLibraryClient(distribution_template=ENTERPRISE_SECURITY_TEMPLATE)
    await client.initialize()
    
    try:
        # Demo user
        user_id = "enterprise_user_123"
        
        # Update security configuration
        await update_security_config(client, user_id)
        logger.info("Security configuration updated")
        
        # Create secure agent
        agent_id = await create_secure_agent(client, user_id)
        logger.info(f"Created secure agent with ID: {agent_id}")
        
        # Create session
        session_id = await client.agents.create_session(agent_id, "Enterprise Security Demo")
        logger.info(f"Created session with ID: {session_id}")
        
        # Interact with agent
        await interact_with_agent(
            client, 
            agent_id, 
            session_id, 
            user_id, 
            "What security features does Llama Stack provide for enterprise use?"
        )
        logger.info("Completed agent interaction")
        
        # Query audit logs
        logs = await query_audit_logs(client, user_id)
        logger.info(f"Retrieved {len(logs)} audit log entries")
        
        # Display sample logs
        for i, log in enumerate(logs[:3]):
            logger.info(f"Log {i+1}: {log.log_type} - {log.action} - {log.status}")
            
    finally:
        # Shutdown client
        await client.shutdown()
        logger.info("Enterprise Security Demo completed")


if __name__ == "__main__":
    asyncio.run(main())

# Enterprise Security Features for Llama Stack

This document outlines the enterprise security features implemented in Llama Stack to ensure secure, compliant, and auditable AI operations in enterprise environments.

## Overview

The enterprise security implementation provides:

1. **Comprehensive Audit Logging**: Track all user interactions, model inferences, and system changes
2. **Configurable Security Levels**: Adjust security controls based on organizational requirements
3. **Enhanced Safety Shields**: Prevent misuse with configurable content filtering
4. **Domain Restrictions**: Limit agent interactions to approved domains
5. **Encryption Controls**: Ensure data is protected at rest and in transit

## Key Components

### 1. Enterprise Security API

The Security API provides centralized management of security configurations and audit logs:

```python
from llama_stack.apis.security import Security, EnterpriseSecurityConfig, SecurityLevel

# Get current security configuration
security_config = await security_api.get_security_config()

# Update security configuration
new_config = EnterpriseSecurityConfig(
    security_level=SecurityLevel.HIGH,
    enable_audit_logging=True,
    audit_log_retention_days=90,
    require_encryption=True,
    allowed_domains=["example.com", "enterprise.org"],
    max_token_lifetime_minutes=30
)
await security_api.update_security_config(new_config)

# Query audit logs
logs = await security_api.query_audit_logs(
    QueryAuditLogsRequest(
        start_time="2025-01-01T00:00:00Z",
        log_types=[AuditLogType.MODEL_INFERENCE, AuditLogType.SECURITY_EVENT],
        limit=100
    )
)
```

### 2. Enhanced Agent Configuration

Agents can be configured with enterprise security settings:

```python
from llama_stack.apis.agents import AgentConfig
from llama_stack.apis.security import SecurityLevel

agent_config = AgentConfig(
    instructions="You are a helpful assistant.",
    security_level=SecurityLevel.HIGH,
    allowed_domains=["enterprise.org"],
    enable_audit_logging=True,
    input_shields=["llama-guard-3-8b"],
    output_shields=["llama-guard-3-8b"]
)
```

### 3. Enterprise Security Distribution

A pre-configured distribution template with enterprise security features:

```python
from llama_stack.templates.enterprise_security import ENTERPRISE_SECURITY_TEMPLATE
from llama_stack.cli.stack.build import build_distribution

# Build an enterprise-grade distribution
build_distribution(
    name="enterprise_ai_solution",
    description="Secure AI solution for enterprise use",
    template=ENTERPRISE_SECURITY_TEMPLATE
)
```

## Security Levels

The system supports multiple security levels:

- **LOW**: Basic security controls for non-sensitive applications
- **MEDIUM**: Standard enterprise security with moderate restrictions
- **HIGH**: Enhanced security for sensitive applications
- **CRITICAL**: Maximum security for highly regulated environments

## Audit Logging

The audit logging system captures:

- User access events
- Model inference requests and responses
- Configuration changes
- Security violations
- Data access patterns

Logs are stored with configurable retention periods and can be queried for compliance reporting.

## Implementation Details

The enterprise security features are implemented across multiple components:

1. **Security API**: Central configuration and audit logging
2. **Enhanced Safety Shields**: LlamaGuard with enterprise-specific categories
3. **Agent Security Controls**: Domain restrictions and token lifetime limits
4. **Telemetry Integration**: Comprehensive tracing for all operations

## Getting Started

To use enterprise security features:

1. Build a distribution using the enterprise security template
2. Configure security settings based on your requirements
3. Implement audit logging in your application
4. Use enhanced agent configurations for secure AI interactions

## Best Practices

- Set appropriate security levels based on data sensitivity
- Configure domain restrictions to limit external interactions
- Enable comprehensive audit logging for compliance
- Regularly review security configurations and audit logs
- Use input and output shields to prevent misuse

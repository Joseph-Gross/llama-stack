# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.

from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, Union, runtime_checkable

from pydantic import BaseModel, Field

from llama_stack.providers.utils.telemetry.trace_protocol import trace_protocol
from llama_stack.schema_utils import json_schema_type, webmethod


class AuthType(Enum):
    """Authentication types supported by the security API.
    
    :cvar OAUTH: OAuth 2.0 authentication
    :cvar OIDC: OpenID Connect authentication
    :cvar API_KEY: API key authentication
    :cvar BASIC: Basic authentication
    :cvar NONE: No authentication
    """
    OAUTH = "oauth"
    OIDC = "oidc"
    API_KEY = "api_key"
    BASIC = "basic"
    NONE = "none"


class AccessLevel(Enum):
    """Access levels for role-based access control.
    
    :cvar ADMIN: Full administrative access
    :cvar WRITE: Read and write access
    :cvar READ: Read-only access
    :cvar NONE: No access
    """
    ADMIN = "admin"
    WRITE = "write"
    READ = "read"
    NONE = "none"


@json_schema_type
class AuthConfig(BaseModel):
    """Configuration for authentication.
    
    :param auth_type: Type of authentication to use
    :param auth_url: URL for authentication service (for OAuth/OIDC)
    :param token_url: URL for token service (for OAuth/OIDC)
    :param client_id: Client ID for OAuth/OIDC
    :param client_secret: Client secret for OAuth/OIDC
    :param scopes: OAuth scopes to request
    :param additional_params: Additional parameters for authentication
    """
    auth_type: AuthType
    auth_url: Optional[str] = None
    token_url: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    scopes: Optional[List[str]] = Field(default_factory=list)
    additional_params: Optional[Dict[str, Any]] = Field(default_factory=dict)


@json_schema_type
class AccessPolicy(BaseModel):
    """Access policy for role-based access control.
    
    :param resource_type: Type of resource (e.g., "model", "agent", "tool")
    :param resource_id: ID of the resource
    :param access_level: Level of access granted
    :param conditions: Optional conditions for access (e.g., time-based restrictions)
    """
    resource_type: str
    resource_id: str
    access_level: AccessLevel
    conditions: Optional[Dict[str, Any]] = Field(default_factory=dict)


@json_schema_type
class Role(BaseModel):
    """Role definition for role-based access control.
    
    :param role_id: Unique identifier for the role
    :param name: Human-readable name for the role
    :param description: Description of the role
    :param policies: Access policies associated with the role
    """
    role_id: str
    name: str
    description: Optional[str] = None
    policies: List[AccessPolicy] = Field(default_factory=list)


@json_schema_type
class User(BaseModel):
    """User definition for authentication and authorization.
    
    :param user_id: Unique identifier for the user
    :param username: Username for the user
    :param email: Email address for the user
    :param roles: Roles assigned to the user
    :param metadata: Additional metadata for the user
    """
    user_id: str
    username: str
    email: Optional[str] = None
    roles: List[str] = Field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


@json_schema_type
class AuditLogEntry(BaseModel):
    """Audit log entry for tracking security-related events.
    
    :param timestamp: Time of the event
    :param user_id: ID of the user who performed the action
    :param action: Action performed
    :param resource_type: Type of resource affected
    :param resource_id: ID of resource affected
    :param status: Status of the action (success/failure)
    :param details: Additional details about the action
    """
    timestamp: str
    user_id: str
    action: str
    resource_type: str
    resource_id: str
    status: str
    details: Optional[Dict[str, Any]] = Field(default_factory=dict)


@json_schema_type
class AuthResponse(BaseModel):
    """Response from authentication request.
    
    :param token: Authentication token
    :param token_type: Type of token (e.g., "Bearer")
    :param expires_in: Token expiration time in seconds
    :param refresh_token: Token for refreshing authentication
    :param user: User information
    """
    token: str
    token_type: str
    expires_in: int
    refresh_token: Optional[str] = None
    user: Optional[User] = None


@json_schema_type
class AuthRequest(BaseModel):
    """Request for authentication.
    
    :param username: Username for authentication
    :param password: Password for authentication
    :param client_id: Client ID for OAuth/OIDC
    :param client_secret: Client secret for OAuth/OIDC
    :param grant_type: Grant type for OAuth/OIDC
    :param refresh_token: Token for refreshing authentication
    """
    username: Optional[str] = None
    password: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    grant_type: Optional[str] = None
    refresh_token: Optional[str] = None


@json_schema_type
class AuthorizationResponse(BaseModel):
    """Response from authorization check.
    
    :param authorized: Whether the action is authorized
    :param reason: Reason for authorization decision
    """
    authorized: bool
    reason: Optional[str] = None


@runtime_checkable
@trace_protocol
class Security(Protocol):
    """Llama Stack Security API for authentication, authorization, and audit logging.
    
    This API provides enterprise-grade security features for Llama Stack:
    - Authentication with various methods (OAuth, OIDC, API keys)
    - Role-based access control for fine-grained permissions
    - Audit logging for security compliance
    - Integration with enterprise identity management systems
    """
    
    @webmethod(route="/security/auth", method="POST")
    async def authenticate(
        self,
        auth_request: AuthRequest,
    ) -> AuthResponse:
        """Authenticate a user and return a token.
        
        :param auth_request: Authentication request details
        :returns: Authentication response with token
        """
        ...
    
    @webmethod(route="/security/auth/refresh", method="POST")
    async def refresh_token(
        self,
        refresh_token: str,
    ) -> AuthResponse:
        """Refresh an authentication token.
        
        :param refresh_token: Token to refresh
        :returns: New authentication response with token
        """
        ...
    
    @webmethod(route="/security/authorize", method="POST")
    async def authorize(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        action: str,
    ) -> AuthorizationResponse:
        """Check if a user is authorized to perform an action on a resource.
        
        :param user_id: ID of the user
        :param resource_type: Type of resource
        :param resource_id: ID of the resource
        :param action: Action to perform
        :returns: Authorization response
        """
        ...
    
    @webmethod(route="/security/roles", method="POST")
    async def create_role(
        self,
        role: Role,
    ) -> Role:
        """Create a new role.
        
        :param role: Role to create
        :returns: Created role
        """
        ...
    
    @webmethod(route="/security/roles/{role_id}", method="GET")
    async def get_role(
        self,
        role_id: str,
    ) -> Role:
        """Get a role by ID.
        
        :param role_id: ID of the role
        :returns: Role
        """
        ...
    
    @webmethod(route="/security/roles/{role_id}", method="PUT")
    async def update_role(
        self,
        role_id: str,
        role: Role,
    ) -> Role:
        """Update a role.
        
        :param role_id: ID of the role
        :param role: Updated role
        :returns: Updated role
        """
        ...
    
    @webmethod(route="/security/roles/{role_id}", method="DELETE")
    async def delete_role(
        self,
        role_id: str,
    ) -> None:
        """Delete a role.
        
        :param role_id: ID of the role
        """
        ...
    
    @webmethod(route="/security/users", method="POST")
    async def create_user(
        self,
        user: User,
    ) -> User:
        """Create a new user.
        
        :param user: User to create
        :returns: Created user
        """
        ...
    
    @webmethod(route="/security/users/{user_id}", method="GET")
    async def get_user(
        self,
        user_id: str,
    ) -> User:
        """Get a user by ID.
        
        :param user_id: ID of the user
        :returns: User
        """
        ...
    
    @webmethod(route="/security/users/{user_id}", method="PUT")
    async def update_user(
        self,
        user_id: str,
        user: User,
    ) -> User:
        """Update a user.
        
        :param user_id: ID of the user
        :param user: Updated user
        :returns: Updated user
        """
        ...
    
    @webmethod(route="/security/users/{user_id}", method="DELETE")
    async def delete_user(
        self,
        user_id: str,
    ) -> None:
        """Delete a user.
        
        :param user_id: ID of the user
        """
        ...
    
    @webmethod(route="/security/audit", method="GET")
    async def get_audit_logs(
        self,
        user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        action: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        limit: Optional[int] = 100,
        offset: Optional[int] = 0,
    ) -> List[AuditLogEntry]:
        """Get audit logs with optional filtering.
        
        :param user_id: Filter by user ID
        :param resource_type: Filter by resource type
        :param resource_id: Filter by resource ID
        :param action: Filter by action
        :param start_time: Filter by start time
        :param end_time: Filter by end time
        :param limit: Maximum number of logs to return
        :param offset: Offset for pagination
        :returns: List of audit log entries
        """
        ...
    
    @webmethod(route="/security/audit", method="POST")
    async def log_audit_event(
        self,
        audit_log: AuditLogEntry,
    ) -> AuditLogEntry:
        """Log an audit event.
        
        :param audit_log: Audit log entry to create
        :returns: Created audit log entry
        """
        ...

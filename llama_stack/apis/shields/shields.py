# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.

"""
Shields API module for Llama Stack.

This module defines the data models and API protocol for working with safety shields
in the Llama Stack framework. It provides functionality for registering, retrieving,
and listing shields that can be used to check content for safety concerns.
"""

# Type annotations
from __future__ import annotations

from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

from pydantic import BaseModel

from llama_stack.apis.resource import Resource, ResourceType
from llama_stack.providers.utils.telemetry.trace_protocol import trace_protocol
from llama_stack.schema_utils import json_schema_type, webmethod


class CommonShieldFields(BaseModel):
    """
    Common fields shared between Shield and ShieldInput models.

    This base class defines the common fields that are used in both the Shield
    and ShieldInput models, providing a consistent structure for shield information.

    Attributes
    ----------
    params : Optional[Dict[str, Any]]
        Optional parameters for configuring the shield, default is None.
    """

    params: Optional[Dict[str, Any]] = None


@json_schema_type
class Shield(CommonShieldFields, Resource):
    """
    Shield resource representing a registered safety shield in the system.

    This class extends CommonShieldFields and Resource to represent a fully
    registered safety shield in the system with its unique identifiers and parameters.
    A safety shield is used to check content for safety concerns.

    Attributes
    ----------
    type : str
        Resource type identifier, always set to ResourceType.shield.value.
    """

    # Using ResourceType as a workaround for Literal[ResourceType.shield.value]
    type: ResourceType = ResourceType.shield

    @property
    def shield_id(self) -> str:
        """
        Get the unique identifier for this shield.

        Returns
        -------
        str
            The unique identifier for this shield.
        """
        return self.identifier

    @property
    def provider_shield_id(self) -> str:
        """
        Get the provider-specific identifier for this shield.

        Returns
        -------
        str
            The provider-specific identifier for this shield.
        """
        return self.provider_resource_id


class ShieldInput(CommonShieldFields):
    """
    Input model for shield registration operations.

    This class extends CommonShieldFields to represent the input data required
    when registering a new safety shield in the system.

    Attributes
    ----------
    shield_id : str
        Unique identifier for the shield.
    provider_id : Optional[str]
        Identifier for the provider of this shield, default is None.
    provider_shield_id : Optional[str]
        Provider-specific identifier for this shield, default is None.
    """

    shield_id: str
    provider_id: Optional[str] = None
    provider_shield_id: Optional[str] = None


class ListShieldsResponse(BaseModel):
    """
    Response model for listing shields.

    This class represents the response structure when listing shields in the system.

    Attributes
    ----------
    data : List[Shield]
        List of Shield objects representing the safety shields in the system.
    """

    data: List[Shield]


@runtime_checkable
@trace_protocol
class Shields(Protocol):
    """
    Protocol defining the Shields API interface.

    This protocol defines the methods that must be implemented by any class
    that provides shield management functionality in the Llama Stack framework.
    It includes methods for registering, retrieving, and listing safety shields.
    """

    @webmethod(route="/shields", method="GET")  # type: ignore[arg-type, type-var]
    async def list_shields(self) -> ListShieldsResponse:  # type: ignore[misc]
        """
        List all shields in the system.

        This method retrieves a list of all safety shields registered in the system.

        Returns
        -------
        ListShieldsResponse
            Response containing a list of all shields in the system.
        """
        ...

    @webmethod(route="/shields/{identifier:path}", method="GET")  # type: ignore[arg-type, type-var]
    async def get_shield(self, identifier: str) -> Optional[Shield]:  # type: ignore[misc]
        """
        Retrieve a shield by its identifier.

        This method retrieves a safety shield from the system using its unique identifier.

        Parameters
        ----------
        identifier : str
            Unique identifier for the shield to retrieve.

        Returns
        -------
        Optional[Shield]
            The retrieved shield if found, None otherwise.
        """
        ...

    @webmethod(route="/shields", method="POST")  # type: ignore[arg-type, type-var]
    async def register_shield(
        self,
        shield_id: str,
        provider_shield_id: Optional[str] = None,
        provider_id: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Shield:  # type: ignore[misc]
        """
        Register a new shield in the system.

        This method registers a new safety shield with the specified parameters in the system.

        Parameters
        ----------
        shield_id : str
            Unique identifier for the shield.
        provider_shield_id : Optional[str], optional
            Provider-specific identifier for this shield, by default None.
        provider_id : Optional[str], optional
            Identifier for the provider of this shield, by default None.
        params : Optional[Dict[str, Any]], optional
            Optional parameters for configuring the shield, by default None.

        Returns
        -------
        Shield
            The newly registered shield.
        """
        ...

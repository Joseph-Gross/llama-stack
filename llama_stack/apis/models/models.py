# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.

"""
Models API module for Llama Stack.

This module defines the data models and API protocol for working with AI models
in the Llama Stack framework. It provides functionality for registering, retrieving,
listing, and unregistering models.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field

from llama_stack.apis.resource import Resource, ResourceType
from llama_stack.providers.utils.telemetry.trace_protocol import trace_protocol
from llama_stack.schema_utils import json_schema_type, webmethod


class CommonModelFields(BaseModel):
    """
    Common fields shared between Model and ModelInput classes.

    This base class defines the common fields that are used in both the Model
    and ModelInput classes, providing a consistent structure for model information.

    Attributes
    ----------
    metadata : Dict[str, Any]
        Additional metadata associated with the model, default is an empty dict.
    """

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Any additional metadata for this model",
    )


@json_schema_type
class ModelType(str, Enum):
    """
    Enumeration of supported model types.

    This enum defines the types of models that can be registered in the system.

    Attributes
    ----------
    llm : str
        Language model type.
    embedding : str
        Embedding model type.
    """

    llm = "llm"
    embedding = "embedding"


@json_schema_type
class Model(CommonModelFields, Resource):
    """
    Model resource representing a registered AI model in the system.

    This class extends CommonModelFields and Resource to represent a fully
    registered model in the system with its unique identifiers and metadata.

    Attributes
    ----------
    type : Literal[ResourceType.model.value]
        Resource type identifier, always set to ResourceType.model.value.
    model_type : ModelType
        Type of the model (llm or embedding), default is ModelType.llm.
    """

    # Using str as a workaround for Literal[ResourceType.model.value]
    type: ResourceType = ResourceType.model

    @property
    def model_id(self) -> str:
        """
        Get the unique identifier for this model.

        Returns
        -------
        str
            The unique identifier for this model.
        """
        return self.identifier

    @property
    def provider_model_id(self) -> str:
        """
        Get the provider-specific identifier for this model.

        Returns
        -------
        str
            The provider-specific identifier for this model.
        """
        return self.provider_resource_id

    model_config = ConfigDict(protected_namespaces=())

    model_type: ModelType = Field(default=ModelType.llm)


class ModelInput(CommonModelFields):
    """
    Input model for model registration operations.

    This class extends CommonModelFields to represent the input data required
    when registering a new model in the system.

    Attributes
    ----------
    model_id : str
        Unique identifier for the model.
    provider_id : Optional[str]
        Identifier for the provider of this model, default is None.
    provider_model_id : Optional[str]
        Provider-specific identifier for this model, default is None.
    model_type : Optional[ModelType]
        Type of the model (llm or embedding), default is ModelType.llm.
    """

    model_id: str
    provider_id: Optional[str] = None
    provider_model_id: Optional[str] = None
    model_type: Optional[ModelType] = ModelType.llm
    model_config = ConfigDict(protected_namespaces=())


class ListModelsResponse(BaseModel):
    """
    Response model for listing models.

    This class represents the response structure when listing models in the system.

    Attributes
    ----------
    data : List[Model]
        List of Model objects representing the models in the system.
    """

    data: List[Model]


@runtime_checkable
@trace_protocol
class Models(Protocol):
    """
    Protocol defining the Models API interface.

    This protocol defines the methods that must be implemented by any class
    that provides model management functionality in the Llama Stack framework.
    It includes methods for registering, retrieving, listing, and unregistering models.
    """

    @webmethod(route="/models", method="GET")  # type: ignore[arg-type, type-var]
    async def list_models(self) -> ListModelsResponse:  # type: ignore[misc]
        """
        List all models in the system.

        This method retrieves a list of all models registered in the system.

        Returns
        -------
        ListModelsResponse
            Response containing a list of all models in the system.
        """
        ...

    @webmethod(route="/models/{model_id:path}", method="GET")  # type: ignore[arg-type, type-var]
    async def get_model(
        self,
        model_id: str,
    ) -> Optional[Model]:  # type: ignore[misc]
        """
        Retrieve a model by its identifier.

        This method retrieves a model from the system using its unique identifier.

        Parameters
        ----------
        model_id : str
            Unique identifier for the model to retrieve.

        Returns
        -------
        Optional[Model]
            The retrieved model if found, None otherwise.
        """
        ...

    @webmethod(route="/models", method="POST")  # type: ignore[arg-type, type-var]
    async def register_model(
        self,
        model_id: str,
        provider_model_id: Optional[str] = None,
        provider_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        model_type: Optional[ModelType] = None,
    ) -> Model:  # type: ignore[misc]
        """
        Register a new model in the system.

        This method registers a new model with the specified parameters in the system.

        Parameters
        ----------
        model_id : str
            Unique identifier for the model.
        provider_model_id : Optional[str], optional
            Provider-specific identifier for this model, by default None.
        provider_id : Optional[str], optional
            Identifier for the provider of this model, by default None.
        metadata : Optional[Dict[str, Any]], optional
            Additional metadata associated with the model, by default None.
        model_type : Optional[ModelType], optional
            Type of the model (llm or embedding), by default None.

        Returns
        -------
        Model
            The newly registered model.
        """
        ...

    @webmethod(route="/models/{model_id:path}", method="DELETE")  # type: ignore[arg-type, type-var]
    async def unregister_model(
        self,
        model_id: str,
    ) -> None:  # type: ignore[misc]
        """
        Unregister a model from the system.

        This method removes a model from the system using its unique identifier.

        Parameters
        ----------
        model_id : str
            Unique identifier for the model to unregister.

        Returns
        -------
        None
        """
        ...

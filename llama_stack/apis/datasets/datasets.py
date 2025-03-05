# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.

"""
Dataset API module for Llama Stack.

This module defines the data models and API protocol for working with datasets
in the Llama Stack framework. It provides functionality for registering, retrieving,
listing, and unregistering datasets.
"""

# Type annotations
from __future__ import annotations

from typing import Any, Dict, List, Optional, Protocol

from pydantic import BaseModel, Field

from llama_stack.apis.common.content_types import URL
from llama_stack.apis.resource import Resource, ResourceType
from llama_stack.schema_utils import json_schema_type, webmethod


class CommonDatasetFields(BaseModel):
    """
    Common fields shared between Dataset and DatasetInput models.

    This base class defines the common fields that are used in both the Dataset
    and DatasetInput models, providing a consistent structure for dataset information.

    Attributes
    ----------
    dataset_schema : Dict[str, ParamType]
        Schema definition for the dataset, specifying the structure and types of data.
    url : URL
        URL where the dataset can be accessed or downloaded from.
    metadata : Dict[str, Any]
        Additional metadata associated with the dataset, default is an empty dict.
    """

    # Using Dict[str, Any] as a workaround for ParamType in type annotations
    dataset_schema: Dict[str, Any]  # Actually Dict[str, ParamType] at runtime
    url: URL
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Any additional metadata for this dataset",
    )


@json_schema_type
class Dataset(CommonDatasetFields, Resource):
    """
    Dataset resource model representing a registered dataset in the system.

    This class extends CommonDatasetFields and Resource to represent a fully
    registered dataset in the system with its unique identifiers and metadata.

    Attributes
    ----------
    type : str
        Resource type identifier, always set to ResourceType.dataset.value.
    """

    # Using ResourceType as a workaround for Literal[ResourceType.dataset.value]
    type: ResourceType = ResourceType.dataset

    @property
    def dataset_id(self) -> str:
        """
        Get the unique identifier for this dataset.

        Returns
        -------
        str
            The unique identifier for this dataset.
        """
        return self.identifier

    @property
    def provider_dataset_id(self) -> str:
        """
        Get the provider-specific identifier for this dataset.

        Returns
        -------
        str
            The provider-specific identifier for this dataset.
        """
        return self.provider_resource_id


class DatasetInput(CommonDatasetFields, BaseModel):
    """
    Input model for dataset registration operations.

    This class extends CommonDatasetFields and BaseModel to represent the input
    data required when registering a new dataset in the system.

    Attributes
    ----------
    dataset_id : str
        Unique identifier for the dataset.
    provider_id : Optional[str]
        Identifier for the provider of this dataset, default is None.
    provider_dataset_id : Optional[str]
        Provider-specific identifier for this dataset, default is None.
    """

    dataset_id: str
    provider_id: Optional[str] = None
    provider_dataset_id: Optional[str] = None


class ListDatasetsResponse(BaseModel):
    """
    Response model for listing datasets.

    This class represents the response structure when listing datasets in the system.

    Attributes
    ----------
    data : List[Dataset]
        List of Dataset objects representing the datasets in the system.
    """

    data: List[Dataset]


class Datasets(Protocol):
    """
    Protocol defining the Dataset API interface.

    This protocol defines the methods that must be implemented by any class
    that provides dataset management functionality in the Llama Stack framework.
    It includes methods for registering, retrieving, listing, and unregistering datasets.
    """

    @webmethod(route="/datasets", method="POST")  # type: ignore[arg-type, type-var]
    async def register_dataset(
        self,
        dataset_id: str,
        dataset_schema: Dict[str, Any],  # Actually Dict[str, ParamType] at runtime
        url: URL,
        provider_dataset_id: Optional[str] = None,
        provider_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:  # type: ignore[misc]
        """
        Register a new dataset in the system.

        This method registers a new dataset with the specified parameters in the system.

        Parameters
        ----------
        dataset_id : str
            Unique identifier for the dataset.
        dataset_schema : Dict[str, ParamType]
            Schema definition for the dataset, specifying the structure and types of data.
        url : URL
            URL where the dataset can be accessed or downloaded from.
        provider_dataset_id : Optional[str], optional
            Provider-specific identifier for this dataset, by default None.
        provider_id : Optional[str], optional
            Identifier for the provider of this dataset, by default None.
        metadata : Optional[Dict[str, Any]], optional
            Additional metadata associated with the dataset, by default None.

        Returns
        -------
        None
        """
        ...

    @webmethod(route="/datasets/{dataset_id:path}", method="GET")  # type: ignore[arg-type, type-var]
    async def get_dataset(
        self,
        dataset_id: str,
    ) -> Optional[Dataset]:  # type: ignore[misc]
        """
        Retrieve a dataset by its identifier.

        This method retrieves a dataset from the system using its unique identifier.

        Parameters
        ----------
        dataset_id : str
            Unique identifier for the dataset to retrieve.

        Returns
        -------
        Optional[Dataset]
            The retrieved dataset if found, None otherwise.
        """
        ...

    @webmethod(route="/datasets", method="GET")  # type: ignore[arg-type, type-var]
    async def list_datasets(self) -> ListDatasetsResponse:  # type: ignore[misc]
        """
        List all datasets in the system.

        This method retrieves a list of all datasets registered in the system.

        Returns
        -------
        ListDatasetsResponse
            Response containing a list of all datasets in the system.
        """
        ...

    @webmethod(route="/datasets/{dataset_id:path}", method="DELETE")  # type: ignore[arg-type, type-var]
    async def unregister_dataset(
        self,
        dataset_id: str,
    ) -> None:  # type: ignore[misc]
        """
        Unregister a dataset from the system.

        This method removes a dataset from the system using its unique identifier.

        Parameters
        ----------
        dataset_id : str
            Unique identifier for the dataset to unregister.

        Returns
        -------
        None
        """
        ...

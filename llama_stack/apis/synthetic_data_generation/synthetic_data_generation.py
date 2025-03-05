# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.

"""
Synthetic Data Generation API module for Llama Stack.

This module defines the data models and API protocol for generating synthetic data
in the Llama Stack framework. It provides functionality for creating synthetic
datasets using various filtering functions and models.
"""

# Type annotations
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Protocol

from pydantic import BaseModel

from llama_stack.apis.inference import Message
from llama_stack.schema_utils import json_schema_type, webmethod


class FilteringFunction(Enum):
    """
    Enumeration of supported filtering functions for synthetic data generation.

    This enum defines the types of filtering functions that can be used to filter
    generated synthetic data based on various criteria.

    Attributes
    ----------
    none : str
        No filtering applied.
    random : str
        Random sampling of generated data.
    top_k : str
        Select top-k results based on score.
    top_p : str
        Select results with cumulative probability above threshold p.
    top_k_top_p : str
        Combination of top-k and top-p filtering.
    sigmoid : str
        Apply sigmoid function to scores for filtering.
    """

    none = "none"
    random = "random"
    top_k = "top_k"
    top_p = "top_p"
    top_k_top_p = "top_k_top_p"
    sigmoid = "sigmoid"


@json_schema_type
class SyntheticDataGenerationRequest(BaseModel):
    """
    Request model for synthetic data generation.

    This class represents the request structure for generating synthetic data,
    including a batch of prompts and a filtering function to apply.

    Attributes
    ----------
    dialogs : List[Message]
        List of message dialogs to use as prompts for synthetic data generation.
    filtering_function : FilteringFunction
        Function to use for filtering generated data, default is FilteringFunction.none.
    model : Optional[str]
        Identifier of the model to use for generation, default is None.
    """

    dialogs: List[Message]  # type: ignore[valid-type]
    filtering_function: FilteringFunction = FilteringFunction.none
    model: Optional[str] = None


@json_schema_type
class SyntheticDataGenerationResponse(BaseModel):
    """
    Response model for synthetic data generation.

    This class represents the response structure from synthetic data generation,
    including a batch of (prompt, response, score) tuples that pass the threshold
    and optional statistics about the generation process.

    Attributes
    ----------
    synthetic_data : List[Dict[str, Any]]
        List of generated synthetic data items, each as a dictionary.
    statistics : Optional[Dict[str, Any]]
        Optional statistics about the generation process, default is None.
    """

    synthetic_data: List[Dict[str, Any]]
    statistics: Optional[Dict[str, Any]] = None


class SyntheticDataGeneration(Protocol):
    """
    Protocol defining the Synthetic Data Generation API interface.

    This protocol defines the methods that must be implemented by any class
    that provides synthetic data generation functionality in the Llama Stack framework.
    """

    @webmethod(route="/synthetic-data-generation/generate")  # type: ignore[arg-type, type-var]
    def synthetic_data_generate(
        self,
        dialogs: List[Message],  # type: ignore[valid-type]
        filtering_function: FilteringFunction = FilteringFunction.none,
        model: Optional[str] = None,
    ) -> SyntheticDataGenerationResponse:  # type: ignore[misc]
        """
        Generate synthetic data based on input dialogs.

        This method generates synthetic data using the provided dialogs as prompts,
        applying the specified filtering function and using the specified model.

        Parameters
        ----------
        dialogs : List[Message]
            List of message dialogs to use as prompts for synthetic data generation.
        filtering_function : FilteringFunction, optional
            Function to use for filtering generated data, default is FilteringFunction.none.
        model : Optional[str], optional
            Identifier of the model to use for generation, default is None.

        Returns
        -------
        SyntheticDataGenerationResponse
            Response containing the generated synthetic data and optional statistics.
        """
        ...

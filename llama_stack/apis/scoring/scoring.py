# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.

"""
Scoring API module for Llama Stack.

This module defines the data models and API protocol for scoring functionality
in the Llama Stack framework. It provides interfaces for scoring individual items
and batches of data using various scoring functions.
"""

# Type annotations
from __future__ import annotations

from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

from pydantic import BaseModel

from llama_stack.apis.scoring_functions import ScoringFn, ScoringFnParams
from llama_stack.schema_utils import json_schema_type, webmethod

# mapping of metric to value
ScoringResultRow = Dict[str, Any]


@json_schema_type
class ScoringResult(BaseModel):
    """
    Model representing the result of a scoring operation.

    This class represents the result of applying a scoring function to one or more
    input rows, including both individual scores and aggregated results.

    Attributes
    ----------
    score_rows : List[ScoringResultRow]
        List of individual scoring results, where each row is a dictionary mapping
        metric names to their values.
    aggregated_results : Dict[str, Any]
        Dictionary of aggregated metrics across all scored rows, mapping metric
        names to their aggregated values.
    """

    score_rows: List[ScoringResultRow]
    # aggregated metrics to value
    aggregated_results: Dict[str, Any]


@json_schema_type
class ScoreBatchResponse(BaseModel):
    """
    Response model for batch scoring operations.

    This class represents the response structure when scoring a batch of data,
    typically from a dataset.

    Attributes
    ----------
    dataset_id : Optional[str]
        Identifier of the dataset that was scored, default is None.
    results : Dict[str, ScoringResult]
        Dictionary mapping scoring function names to their respective results.
    """

    dataset_id: Optional[str] = None
    results: Dict[str, ScoringResult]


@json_schema_type
class ScoreResponse(BaseModel):
    """
    Response model for individual scoring operations.

    This class represents the response structure when scoring individual input rows.

    Attributes
    ----------
    results : Dict[str, ScoringResult]
        Dictionary mapping scoring function names to their respective results.
        Each key in the dict is a scoring function name.
    """

    # each key in the dict is a scoring function name
    results: Dict[str, ScoringResult]


class ScoringFunctionStore(Protocol):
    """
    Protocol for a store of scoring functions.

    This protocol defines the interface for a store that provides access to
    scoring functions by their identifiers.
    """

    def get_scoring_function(self, scoring_fn_id: str) -> ScoringFn:
        """
        Retrieve a scoring function by its identifier.

        Parameters
        ----------
        scoring_fn_id : str
            Identifier of the scoring function to retrieve.

        Returns
        -------
        ScoringFn
            The scoring function corresponding to the given identifier.
        """
        ...


@runtime_checkable
class Scoring(Protocol):
    """
    Protocol defining the Scoring API interface.

    This protocol defines the methods that must be implemented by any class
    that provides scoring functionality in the Llama Stack framework. It includes
    methods for scoring individual items and batches of data.
    """

    scoring_function_store: ScoringFunctionStore

    @webmethod(route="/scoring/score-batch", method="POST")  # type: ignore[arg-type, type-var]
    async def score_batch(
        self,
        dataset_id: str,
        scoring_functions: Dict[str, Optional[ScoringFnParams]],  # type: ignore[valid-type]
        save_results_dataset: bool = False,
    ) -> ScoreBatchResponse:
        """
        Score a batch of data from a dataset.

        This method applies multiple scoring functions to a batch of data from
        a dataset and returns the results.

        Parameters
        ----------
        dataset_id : str
            Identifier of the dataset to score.
        scoring_functions : Dict[str, Optional[ScoringFnParams]]
            Dictionary mapping scoring function names to their parameters.
            If a value is None, default parameters will be used.
        save_results_dataset : bool, optional
            Whether to save the scoring results as a new dataset, by default False.

        Returns
        -------
        ScoreBatchResponse
            Response containing the results of applying the scoring functions
            to the dataset.
        """
        ...

    @webmethod(route="/scoring/score", method="POST")  # type: ignore[arg-type, type-var]
    async def score(
        self,
        input_rows: List[Dict[str, Any]],
        scoring_functions: Dict[str, Optional[ScoringFnParams]],  # type: ignore[valid-type]
    ) -> ScoreResponse:
        """
        Score individual input rows.

        This method applies multiple scoring functions to a list of input rows
        and returns the results.

        Parameters
        ----------
        input_rows : List[Dict[str, Any]]
            List of input rows to score, where each row is a dictionary of values.
        scoring_functions : Dict[str, Optional[ScoringFnParams]]
            Dictionary mapping scoring function names to their parameters.
            If a value is None, default parameters will be used.

        Returns
        -------
        ScoreResponse
            Response containing the results of applying the scoring functions
            to the input rows.
        """
        ...

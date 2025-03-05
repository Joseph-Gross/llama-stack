# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.
# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

from pydantic import BaseModel, Field

# Import Any instead of InterleavedContent to avoid circular imports
from llama_stack.apis.vector_dbs import VectorDB
from llama_stack.providers.utils.telemetry.trace_protocol import trace_protocol
from llama_stack.schema_utils import json_schema_type, webmethod


class Chunk(BaseModel):
    content: Any  # Use Any instead of InterleavedContent to avoid circular imports
    metadata: Dict[str, Any] = Field(default_factory=dict)


@json_schema_type
class QueryChunksResponse(BaseModel):
    chunks: List[Chunk]
    scores: List[float]


class VectorDBStore(Protocol):
    def get_vector_db(self, vector_db_id: str) -> Optional[VectorDB]: ...


@runtime_checkable
@trace_protocol
class VectorIO(Protocol):
    vector_db_store: VectorDBStore

    # this will just block now until chunks are inserted, but it should
    # probably return a Job instance which can be polled for completion
    # Protocol methods should not have decorators
    async def insert_chunks(
        self,
        vector_db_id: str,
        chunks: List[Chunk],
        ttl_seconds: Optional[int] = None,
    ) -> None: ...

    # Protocol methods should not have decorators
    async def query_chunks(
        self,
        vector_db_id: str,
        query: Any,  # Use Any instead of InterleavedContent to avoid circular imports
        params: Optional[Dict[str, Any]] = None,
    ) -> QueryChunksResponse: ...

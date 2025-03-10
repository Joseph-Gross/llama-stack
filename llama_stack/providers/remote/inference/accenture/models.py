# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.

from llama_stack.apis.models.models import ModelType
from llama_stack.models.llama.datatypes import CoreModelId
from llama_stack.providers.utils.inference.model_registry import (
    ProviderModelEntry,
    build_hf_repo_model_entry,
)

MODEL_ENTRIES = [
    # Map Accenture models to Llama models
    build_hf_repo_model_entry(
        "accenture/accenture-llm-large",
        CoreModelId.llama3_1_70b_instruct.value,
    ),
    build_hf_repo_model_entry(
        "accenture/accenture-llm-base",
        CoreModelId.llama3_1_8b_instruct.value,
    ),
    # Add Accenture-specific embedding model
    ProviderModelEntry(
        provider_model_id="accenture/accenture-embedding-model",
        model_type=ModelType.embedding,
        metadata={
            "embedding_dimension": 768,
            "context_length": 8192,
        },
    ),
]

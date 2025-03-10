# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.

from llama_stack.distribution.datatypes import (
    Api,
    DistributionTemplate,
    InlineProviderSpec,
    StackRunConfig,
)

ENTERPRISE_SECURITY_TEMPLATE = DistributionTemplate(
    name="enterprise_security",
    description="Enterprise-grade security distribution with enhanced safety features, audit logging, and compliance controls",
    providers=[
        InlineProviderSpec(
            api=Api.inference,
            provider_module="llama_stack.providers.inline.inference.meta_reference",
            config={
                "model_registry": {
                    "llama-3-8b": "meta-llama/Meta-Llama-3-8B",
                    "llama-3-70b": "meta-llama/Meta-Llama-3-70B",
                }
            },
        ),
        InlineProviderSpec(
            api=Api.safety,
            provider_module="llama_stack.providers.inline.safety.llama_guard",
            config={
                "excluded_categories": [],
                "security_level": "high",
                "enable_enhanced_logging": True,
                "enterprise_mode": True,
            },
        ),
        InlineProviderSpec(
            api=Api.security,
            provider_module="llama_stack.providers.inline.security.meta_reference",
            config={
                "storage_path": "enterprise_security_store",
                "enable_encryption": True,
            },
        ),
        InlineProviderSpec(
            api=Api.telemetry,
            provider_module="llama_stack.providers.inline.telemetry.meta_reference",
            config={
                "enable_tracing": True,
                "span_processor": "sqlite",
                "sqlite_path": "enterprise_telemetry.db",
                "retention_days": 90,
            },
        ),
        InlineProviderSpec(
            api=Api.agents,
            provider_module="llama_stack.providers.inline.agents.meta_reference",
            config={
                "default_model": "llama-3-8b",
                "default_shields": ["llama-guard-3-8b"],
            },
        ),
        InlineProviderSpec(
            api=Api.shields,
            provider_module="llama_stack.providers.inline.safety.llama_guard",
            config={},
        ),
        InlineProviderSpec(
            api=Api.vector_io,
            provider_module="llama_stack.providers.inline.vector_io.meta_reference",
            config={},
        ),
        InlineProviderSpec(
            api=Api.tool_runtime,
            provider_module="llama_stack.providers.inline.tool_runtime.meta_reference",
            config={},
        ),
        InlineProviderSpec(
            api=Api.tool_groups,
            provider_module="llama_stack.providers.inline.tool_runtime.meta_reference",
            config={},
        ),
    ],
    default_run_config=StackRunConfig(
        host="localhost",
        port=8000,
        log_level="info",
        enable_security=True,
        security_level="high",
    ),
)

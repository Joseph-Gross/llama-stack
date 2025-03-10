# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.

from pydantic import BaseModel

from .config import AccentureImplConfig


class AccentureProviderDataValidator(BaseModel):
    accenture_api_key: str


async def get_adapter_impl(config: AccentureImplConfig, _deps):
    from .accenture import AccentureInferenceAdapter

    assert isinstance(config, AccentureImplConfig), f"Unexpected config type: {type(config)}"
    impl = AccentureInferenceAdapter(config)
    await impl.initialize()
    return impl

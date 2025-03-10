# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.

import base64
import io
import logging
from urllib.parse import unquote

import pandas

from llama_stack.apis.common.content_types import URL
from llama_stack.providers.utils.memory.vector_store import parse_data_url, _is_safe_url

log = logging.getLogger(__name__)


def get_dataframe_from_url(url: URL):
    # Validate URL before processing
    if not _is_safe_url(url.uri):
        raise ValueError(f"Unsafe URL provided: {url.uri}")
        
    df = None
    try:
        if url.uri.endswith(".csv"):
            df = pandas.read_csv(url.uri)
        elif url.uri.endswith(".xlsx"):
            df = pandas.read_excel(url.uri)
        elif url.uri.startswith("data:"):
            parts = parse_data_url(url.uri)
            data = parts["data"]
            if parts["is_base64"]:
                data = base64.b64decode(data)
            else:
                data = unquote(data)
                encoding = parts["encoding"] or "utf-8"
                data = data.encode(encoding)

            mime_type = parts["mimetype"]
            mime_category = mime_type.split("/")[0]
            data_bytes = io.BytesIO(data)

            if mime_category == "text":
                df = pandas.read_csv(data_bytes)
            else:
                df = pandas.read_excel(data_bytes)
        else:
            raise ValueError(f"Unsupported file type: {url}")
    except Exception as e:
        log.error(f"Error processing URL {url.uri}: {str(e)}")
        raise ValueError(f"Error processing URL: {str(e)}")

    return df

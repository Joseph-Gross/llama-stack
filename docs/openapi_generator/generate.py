# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.

# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described found in the
# LICENSE file in the root directory of this source tree.

from datetime import datetime
from pathlib import Path

import fire
import ruamel.yaml as yaml

from llama_stack.apis.version import LLAMA_STACK_API_VERSION  # noqa: E402
from llama_stack.distribution.stack import LlamaStack  # noqa: E402

from typing import Any, Dict, Optional

from .pyopenapi.options import Options  # noqa: E402
from .pyopenapi.specification import Info, Server  # noqa: E402
from .pyopenapi.utility import Specification  # noqa: E402


def str_presenter(dumper: Any, data: str) -> Any:
    """
    Custom YAML presenter for string data.
    
    Args:
        dumper: YAML dumper instance
        data: String data to be presented
        
    Returns:
        YAML scalar representation with appropriate style
    """
    if data.startswith(f"/{LLAMA_STACK_API_VERSION}") or data.startswith(
        "#/components/schemas/"
    ):
        style = None
    else:
        style = ">" if "\n" in data or len(data) > 40 else None
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style=style)


def main(output_dir: str) -> None:
    """
    Generate OpenAPI specification files in YAML and HTML formats.
    
    Args:
        output_dir: Directory path where the generated files will be saved
        
    Raises:
        ValueError: If the output directory does not exist
    """
    output_path = Path(output_dir)
    if not output_path.exists():
        raise ValueError(f"Directory {output_dir} does not exist")

    now = str(datetime.now())
    print(
        "Converting the spec to YAML (openapi.yaml) and HTML (openapi.html) at " + now
    )
    print("")
    spec = Specification(
        LlamaStack,
        Options(
            server=Server(url="http://any-hosted-llama-stack.com"),
            info=Info(
                title="Llama Stack Specification",
                version=LLAMA_STACK_API_VERSION,
                description="""# Llama Stack API Specification

This is the comprehensive specification of the Llama Stack API that provides
a set of endpoints and their corresponding interfaces that are tailored to
best leverage Llama Models.

## API Overview

The Llama Stack API is organized into several modules:

- **Inference**: Generate text, embeddings, and chat completions
- **Safety**: Content moderation and safety filtering
- **Agents**: Agent-based interactions and tool usage
- **Vector IO**: Vector database operations
- **Dataset IO**: Dataset management and operations
- **Scoring**: Evaluation metrics and scoring
- **Eval**: Model evaluation and benchmarking
- **Tool Runtime**: Tool execution environment
- **Telemetry**: Logging and monitoring

## Authentication

API requests require authentication using an API key provided in the
`Authorization` header as a Bearer token.

## Error Handling

All API endpoints return standard error responses with appropriate
HTTP status codes and detailed error messages.
""",
            ),
        ),
    )

    try:
        yaml_file_path = output_path / "llama-stack-spec.yaml"
        with open(yaml_file_path, "w", encoding="utf-8") as fp:
            y = yaml.YAML()
            y.default_flow_style = False
            y.block_seq_indent = 2
            y.map_indent = 2
            y.sequence_indent = 4
            y.sequence_dash_offset = 2
            y.width = 80
            y.allow_unicode = True
            y.representer.add_representer(str, str_presenter)

            y.dump(
                spec.get_json(),
                fp,
            )
        print(f"YAML specification written to {yaml_file_path}")
    except Exception as e:
        print(f"Error writing YAML specification: {e}")

    try:
        html_file_path = output_path / "llama-stack-spec.html"
        with open(html_file_path, "w", encoding="utf-8") as fp:
            spec.write_html(fp, pretty_print=True)
        print(f"HTML specification written to {html_file_path}")
    except Exception as e:
        print(f"Error writing HTML specification: {e}")


if __name__ == "__main__":
    fire.Fire(main)

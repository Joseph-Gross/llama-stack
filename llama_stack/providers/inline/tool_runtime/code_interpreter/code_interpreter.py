# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import logging
import os
import shutil
import tempfile
from typing import Any, Dict, List, Optional

from llama_stack.apis.common.content_types import URL
from llama_stack.apis.tools import (
    Tool,
    ToolDef,
    ToolInvocationResult,
    ToolParameter,
    ToolRuntime,
)
from llama_stack.providers.datatypes import ToolsProtocolPrivate

from .code_execution import CodeExecutionContext, CodeExecutionRequest, CodeExecutor
from .config import CodeInterpreterToolConfig

log = logging.getLogger(__name__)


class CodeInterpreterToolRuntimeImpl(ToolsProtocolPrivate, ToolRuntime):
    def __init__(self, config: CodeInterpreterToolConfig):
        self.config = config
        
        # Create a secure temporary directory with restricted permissions
        temp_dir = tempfile.mkdtemp()
        os.chmod(temp_dir, 0o700)  # Restrict permissions to owner only
        
        ctx = CodeExecutionContext(
            matplotlib_dump_dir=temp_dir,
        )
        self.code_executor = CodeExecutor(ctx)
        
        # Track temporary directories for cleanup
        self._temp_dirs = [temp_dir]
        
    def __del__(self):
        """Clean up temporary directories when the object is garbage collected."""
        for temp_dir in self._temp_dirs:
            try:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
            except Exception as e:
                logging.error(f"Failed to clean up temporary directory {temp_dir}: {e}")

    async def initialize(self):
        pass

    async def register_tool(self, tool: Tool):
        pass

    async def unregister_tool(self, tool_id: str) -> None:
        return

    async def list_runtime_tools(
        self, tool_group_id: Optional[str] = None, mcp_endpoint: Optional[URL] = None
    ) -> List[ToolDef]:
        return [
            ToolDef(
                name="code_interpreter",
                description="Execute code",
                parameters=[
                    ToolParameter(
                        name="code",
                        description="The code to execute",
                        parameter_type="string",
                    ),
                ],
            )
        ]

    async def invoke_tool(self, tool_name: str, kwargs: Dict[str, Any]) -> ToolInvocationResult:
        script = kwargs["code"]
        req = CodeExecutionRequest(scripts=[script])
        res = self.code_executor.execute(req)
        pieces = [res["process_status"]]
        for out_type in ["stdout", "stderr"]:
            res_out = res[out_type]
            if res_out != "":
                pieces.extend([f"[{out_type}]", res_out, f"[/{out_type}]"])
                if out_type == "stderr":
                    log.error(f"ipython tool error: ↓\n{res_out}")
        return ToolInvocationResult(content="\n".join(pieces))

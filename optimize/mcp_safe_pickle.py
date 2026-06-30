from llama_index.tools.mcp import BasicMCPClient, McpToolSpec
from llama_index.core.tools.function_tool import FunctionTool
from llama_index.core.tools.types import ToolMetadata

# -- Existing GetState Shields --
BasicMCPClient.__getstate__ = lambda self: {"status": "mcp_shielded"}
FunctionTool.__getstate__ = lambda self: {k: v for k, v in self.__dict__.items() if k not in ['fn', 'async_fn']}
ToolMetadata.__getstate__ = lambda self: {k: v for k, v in self.__dict__.items() if k != 'fn_schema'}

# 🛡️ NEW: Deepcopy Shields for the Workflow Checkpointer
# This forces Pydantic to pass the live clients by reference instead of trying to clone them
BasicMCPClient.__deepcopy__ = lambda self, memo: self
McpToolSpec.__deepcopy__ = lambda self, memo: self

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


from llama_index.core.base.llms.base import BaseLLM
from llama_index.core.tools.function_tool import FunctionTool
from llama_index.tools.mcp import BasicMCPClient

# 1. The Universal Pass-by-Reference Function
def bypass_pydantic_clone(self, *args, **kwargs):
    """Forces Pydantic to use the existing memory reference instead of cloning."""
    return self

# 2. Shield the LLM (Stops pickling the live httpx connection to your local model)
BaseLLM.__deepcopy__ = bypass_pydantic_clone
if hasattr(BaseLLM, 'model_copy'):
    BaseLLM.model_copy = bypass_pydantic_clone

# 3. Shield the Tools & Wrappers
FunctionTool.__deepcopy__ = bypass_pydantic_clone
if hasattr(FunctionTool, 'model_copy'):
    FunctionTool.model_copy = bypass_pydantic_clone

# 4. Shield the MCP Client
BasicMCPClient.__deepcopy__ = bypass_pydantic_clone
if hasattr(BasicMCPClient, 'model_copy'):
    BasicMCPClient.model_copy = bypass_pydantic_clone

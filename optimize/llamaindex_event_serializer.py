from llama_index.tools.mcp import BasicMCPClient
from llama_index.core.tools.function_tool import FunctionTool

# 🛡️ SHIELD 1: Make the MCP Client invisible to the Workflow Checkpointer
def safe_mcp_getstate(self):
    return {"status": "mcp_connection_ignored_for_workflow_snapshot"}

BasicMCPClient.__getstate__ = safe_mcp_getstate

# 🛡️ SHIELD 2: Make the Tool functions safe
# Sometimes FunctionTool closures hold module references that crash the pickler
def safe_tool_getstate(self):
    state = self.__dict__.copy()
    # Remove the un-pickleable raw function reference from the snapshot
    if 'fn' in state:
        state['fn'] = None 
    if 'async_fn' in state:
        state['async_fn'] = None
    return state

FunctionTool.__getstate__ = safe_tool_getstate

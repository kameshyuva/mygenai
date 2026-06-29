import json
import csv
import io
from llama_index.tools.mcp import BasicMCPClient, McpToolSpec
from llama_index.core.tools.function_tool import FunctionTool

# ==========================================
# 1. CORE INSTRUMENTATION SHIELDS
# ==========================================
# Stop span_safe_call from crawling into the live MCP sockets
BasicMCPClient.__getstate__ = lambda self: {"status": "mcp_connection_shielded"}

def safe_tool_getstate(self):
    state = self.__dict__.copy()
    # Nullify the function references specifically during the instrumentation snapshot
    if 'fn' in state: state['fn'] = None 
    if 'async_fn' in state: state['async_fn'] = None
    return state

FunctionTool.__getstate__ = safe_tool_getstate

# ==========================================
# 2. TOKEN-REDUCING CSV FORMATTER
# ==========================================
def format_json_to_csv(raw_output) -> str:
    """Converts a JSON string or dict/list into a dense CSV string."""
    try:
        data = json.loads(raw_output) if isinstance(raw_output, str) else raw_output
        
        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(data[0].keys())
            for item in data:
                writer.writerow(item.values())
                
            csv_str = output.getvalue()
            output.close()
            return csv_str
            
        return str(raw_output)
    except Exception:
        return str(raw_output)

# ==========================================
# 3. THE PICKLE-SAFE CALLABLE (CRITICAL FIX)
# ==========================================
# Defined at the top-level of the module so `span_safe_call` can serialize it
class CsvOptimizedMcpCallable:
    def __init__(self, original_mcp_fn):
        self.original_mcp_fn = original_mcp_fn

    def __getstate__(self):
        # When span_safe_call inspects this argument, return a safe empty state
        # instead of trying to serialize the live MCP bound method
        return {}

    def __setstate__(self, state):
        pass

    async def __call__(self, *args, **kwargs):
        # 1. Execute the actual MCP JSON-RPC call
        raw_response = await self.original_mcp_fn(*args, **kwargs)
        
        # 2. Convert directly to CSV to reduce token usage
        return format_json_to_csv(raw_response)

# ==========================================
# 4. TOOL EXTRACTION
# ==========================================
async def get_csv_optimized_mcp_tools(mcp_client: BasicMCPClient) -> list[FunctionTool]:
    mcp_tool_spec = McpToolSpec(client=mcp_client)
    raw_tools = await mcp_tool_spec.to_tool_list_async()
    
    csv_tools = []
    
    for tool in raw_tools:
        # Wrap the live MCP function in our pickle-safe class
        safe_callable = CsvOptimizedMcpCallable(tool.async_fn)
        
        csv_tool = FunctionTool.from_defaults(
            async_fn=safe_callable,
            name=tool.metadata.name,
            description=tool.metadata.description,
            fn_schema=tool.metadata.fn_schema 
        )
        csv_tools.append(csv_tool)
        
    return csv_tools

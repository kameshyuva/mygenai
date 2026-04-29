from llama_index.core.agent import FunctionCallingAgent
from llama_index.core.tools import McpToolSpec
# Import your BasicMcpClient (assuming from llama-index-tools-mcp)
from llama_index.tools.mcp import BasicMcpClient 

# 1. Create a simplified client that auto-nests arguments
class AutoNestingMcpClient(BasicMcpClient):
    def call_tool(self, tool_name: str, arguments: dict, *args, **kwargs):
        # If the LLM output flat arguments, nest them!
        if "request" not in arguments:
            arguments = {"request": arguments}
        
        # Pass the formatted payload to the actual MCP server
        return super().call_tool(tool_name, arguments, *args, **kwargs)

    async def acall_tool(self, tool_name: str, arguments: dict, *args, **kwargs):
        # Same for async
        if "request" not in arguments:
            arguments = {"request": arguments}
            
        return await super().acall_tool(tool_name, arguments, *args, **kwargs)

# 2. Use your custom client
mcp_client = AutoNestingMcpClient(...) # Initialize with your server details

# 3. Load tools normally
mcp_tool_spec = McpToolSpec(client=mcp_client)
tools = mcp_tool_spec.to_tool_list()

# 4. Run the fast FunctionCallingAgent without schema hacks
agent = FunctionCallingAgent.from_tools(
    tools,
    llm=llm,
    verbose=True
)

from llama_index.tools.mcp import McpToolSpec
# (Assume basic_mcp_client is already initialized and connected)

# 1. Load the raw tools from your MCP server
mcp_spec = McpToolSpec(client=basic_mcp_client)
raw_mcp_tools = mcp_spec.to_tool_list()

# 2. Programmatically wrap every tool in the list
optimized_tools = [wrap_tool_for_markdown(tool) for tool in raw_mcp_tools]

# 3. Initialize your agent with the optimized tools
# agent = FunctionAgent(tools=optimized_tools, llm=your_llm, memory=your_memory_module)

# Now, when you call agent.run(), the MCP tools are executed, but the JSON 
# is stripped and formatted into Markdown before hitting the memory module.

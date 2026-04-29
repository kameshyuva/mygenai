from pydantic import Field, create_model
from llama_index.core.agent import ReActAgent

# 1. Initialize your client and spec as you already do
# mcp_client = BasicMcpClient(...)
# mcp_tool_spec = McpToolSpec(client=mcp_client)

# 2. Extract the base tools
tools = mcp_tool_spec.to_tool_list()

# 3. Intercept and wrap the schema for every tool
for tool in tools:
    original_schema = tool.metadata.fn_schema
    
    # Programmatically create a new Pydantic schema: { "request": { <OriginalSchema> } }
    WrappedSchema = create_model(
        f"{tool.metadata.name}Wrapper",
        request=(
            original_schema, 
            Field(..., description="REQUIRED: You MUST nest all tool arguments inside this 'request' object. Do not output flat arguments.")
        )
    )
    
    # Overwrite the tool's schema metadata
    tool.metadata.fn_schema = WrappedSchema

# 4. Pass the modified tools to your agent
agent = ReActAgent.from_tools(
    tools,
    llm=llm,
    memory=memory,
    verbose=True
)

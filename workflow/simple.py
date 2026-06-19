from llama_index.core.agent.workflow import AgentWorkflow

# 1. You already have your agent worker
# agent = FunctionAgent(
#     name="mcp_agent", 
#     description="Useful for MCP tools",
#     llm=your_llm,
#     tool_retriever=ensemble_tool_retriever
# )

# 2. Wrap it in the official Workflow manager
workflow = AgentWorkflow(
    agents=[agent], 
    root_agent=agent.name # Make sure this matches the 'name' you gave your FunctionAgent
)

# 3. Run the workflow asynchronously using the strict kwarg!
response = await workflow.run(user_msg="Your prompt goes here")

print(response)

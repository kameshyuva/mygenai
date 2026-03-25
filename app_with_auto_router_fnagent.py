import asyncio
from llama_index.llms.ollama import Ollama
from llama_index.tools.mcp import BasicMCPClient, McpToolSpec

# 1. NEW IMPORT: Use the Workflow-based FunctionAgent
from llama_index.core.agent.workflow import FunctionAgent

# Import our custom auto-tuning semantic router
from auto_router import AutoTuningRouter

async def main():
    # Initialize the LLM
    llm = Ollama(model="llama3.2", request_timeout=120.0, temperature=0.0)
    
    # Connect to the local SQLite MCP Server
    print("Connecting to MCP Server...")
    mcp_client = BasicMCPClient("http://localhost:8000/sse")
    mcp_tool_spec = McpToolSpec(client=mcp_client)
    mcp_tools = await mcp_tool_spec.to_tool_list_async()
    
    # 2. NEW INSTANTIATION: Direct initialization, no 'from_tools' or 'verbose'
    agent = FunctionAgent(
        tools=mcp_tools, 
        llm=llm,
        system_prompt="You are a helpful data analyst. Use your tools to answer user queries."
    )

    # Initialize the Semantic Router
    router = AutoTuningRouter(
        redis_url="redis://localhost:6379",
        embedding_model="nomic-embed-text",
        distance_threshold=0.20
    )

    async def execute_query(query: str):
        print(f"\n=========================================")
        print(f"USER: {query}")
        
        # --- FAST PATH: Check Redis for a known route ---
        target_tool_name = router.get_cached_tool(query)
        
        if target_tool_name:
            print(f"⚡ FAST PATH: Routing directly to '{target_tool_name}'")
            selected_tool = next(t for t in mcp_tools if t.metadata.name == target_tool_name)
            
            try:
                # Bypass the agent and use the LLM just to extract JSON arguments
                tool_kwargs = await router.extract_arguments(query, selected_tool.metadata.fn_schema_str, llm)
                
                # Execute the tool locally
                result = selected_tool.fn(**tool_kwargs)
                print(f"✅ EXECUTION RESULT:\n{result}")
                return
            
            except ValueError as e:
                print(f"Argument extraction failed: {e}. Falling back to Slow Path...")

        # --- SLOW PATH: First time seeing this intent ---
        print("☁️ SLOW PATH: Executing Function Agent Workflow...")
        
        # 3. NEW EXECUTION: Use .run() instead of .achat()
        response = await agent.run(query)
        print(f"✅ AGENT ANSWER:\n{str(response)}")
        
        # --- LEARN: Cache the Agent's decision for next time ---
        # Note: In the new Workflow architecture, to get the exact tool name robustly 
        # in production, you would listen to `ToolCall` events in the agent stream. 
        # For this script, we can parse the response's memory if a tool was used.
        try:
            # Check the agent's memory for the most recent tool call
            history = await agent.memory.get()
            if history and hasattr(history[-1], 'additional_kwargs') and 'tool_calls' in history[-1].additional_kwargs:
                used_tool = history[-1].additional_kwargs['tool_calls'][0].function.name
                print(f"🧠 LEARNING: Saving route for '{used_tool}'")
                router.learn_route(query, used_tool)
        except Exception as e:
            # Failsafe if it was a standard conversation without tools
            pass

    # --- Execution Tests ---
    
    # Test 1: The system has to figure it out and learn (Slow Path)
    await execute_query("Can you tell me the average salary in the Sales department?")
    
    # Test 2: The system instantly knows what to do based on Test 1 (Fast Path)
    await execute_query("What's the average salary for the Engineering team?")

if __name__ == "__main__":
    asyncio.run(main())

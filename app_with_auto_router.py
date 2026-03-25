import asyncio
from llama_index.llms.ollama import Ollama
from llama_index.core.agent import ReActAgent
from llama_index.tools.mcp import BasicMCPClient, McpToolSpec

# Import our reusable class
from auto_router import AutoTuningRouter

async def main():
    # 1. Initialize core components
    llm = Ollama(model="llama3.2", request_timeout=120.0, temperature=0.0)
    
    mcp_client = BasicMCPClient("http://localhost:8000/sse")
    mcp_tool_spec = McpToolSpec(client=mcp_client)
    mcp_tools = await mcp_tool_spec.to_tool_list_async()
    
    agent = ReActAgent.from_tools(tools=mcp_tools, llm=llm, verbose=False)

    # 2. Initialize our custom Router
    router = AutoTuningRouter(
        redis_url="redis://localhost:6379",
        embedding_model="nomic-embed-text",
        distance_threshold=0.20
    )

    async def execute_query(query: str):
        print(f"\nUSER: {query}")
        
        # --- FAST PATH: Check the Router ---
        target_tool_name = router.get_cached_tool(query)
        
        if target_tool_name:
            print(f"⚡ FAST PATH: Routing directly to '{target_tool_name}'")
            selected_tool = next(t for t in mcp_tools if t.metadata.name == target_tool_name)
            
            try:
                # Use the router's utility method to quickly grab the JSON args
                tool_kwargs = await router.extract_arguments(query, selected_tool.metadata.fn_schema_str, llm)
                print(f"Extracted Args: {tool_kwargs}")
                
                result = selected_tool.fn(**tool_kwargs)
                print(f"✅ EXECUTION RESULT:\n{result}")
                return
            
            except ValueError as e:
                print(f"Argument extraction failed: {e}. Falling back to Slow Path...")

        # --- SLOW PATH: Let the Agent figure it out ---
        print("☁️ SLOW PATH: Unknown intent. Executing ReAct Agent...")
        response = await agent.achat(query)
        print(f"✅ AGENT ANSWER:\n{response.response}")
        
        # --- LEARN: Cache the Agent's decision for next time ---
        if response.sources:
            used_tool = response.sources[0].tool_name
            print(f"🧠 LEARNING: Saving route for '{used_tool}'")
            router.learn_route(query, used_tool)

    # --- Execution ---
    await execute_query("Add David to the Marketing team with a 75000 salary.")
    await execute_query("Please hire Jessica into the Marketing department at 80000.")

if __name__ == "__main__":
    asyncio.run(main())

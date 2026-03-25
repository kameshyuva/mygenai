import asyncio
import json
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.core.agent import ReActAgent
from llama_index.tools.mcp import BasicMCPClient, McpToolSpec
from redisvl.extensions.llmcache import SemanticCache
from redisvl.utils.vectorize import CustomTextVectorizer

async def main():
    # 1. Initialize Local Models
    llm = Ollama(model="llama3.2", request_timeout=120.0, temperature=0.0)
    embed_model = OllamaEmbedding(model_name="nomic-embed-text")
    vectorizer = CustomTextVectorizer(embed=embed_model.get_text_embedding)

    # 2. Connect to the MCP Server
    mcp_client = BasicMCPClient("http://localhost:8000/sse")
    mcp_tool_spec = McpToolSpec(client=mcp_client)
    mcp_tools = await mcp_tool_spec.to_tool_list_async()

    # 3. Initialize the ReAct Agent (The "Slow Path")
    agent = ReActAgent.from_tools(tools=mcp_tools, llm=llm, verbose=False)

    # 4. Initialize the Redis Cache
    # We use a slightly looser threshold (0.20) so the cache catches more variations
    redis_cache = SemanticCache(
        name="dynamic_tool_router",
        redis_url="redis://localhost:6379",
        distance_threshold=0.20,
        vectorizer=vectorizer
    )

    async def execute_smart_query(query: str):
        print(f"\n=========================================")
        print(f"USER: {query}")
        
        # --- FAST PATH: Check Redis for a known tool route ---
        cache_hit = redis_cache.check(prompt=query)
        
        if cache_hit:
            # We found a match! We extract the tool name we saved previously.
            target_tool_name = cache_hit[0]['response']
            print(f"⚡ FAST PATH: Semantic match found! Routing directly to '{target_tool_name}'")
            
            selected_tool = next(t for t in mcp_tools if t.metadata.name == target_tool_name)
            
            # Use the LLM *only* to extract arguments, skipping the ReAct loop
            prompt = (
                f"Extract the arguments from this query: '{query}'\n"
                f"To fit this tool schema: {selected_tool.metadata.fn_schema_str}\n"
                "Return ONLY valid JSON. No markdown."
            )
            llm_response = await llm.acomplete(prompt)
            
            try:
                tool_kwargs = json.loads(llm_response.text)
                result = selected_tool.fn(**tool_kwargs)
                print(f"✅ EXECUTION RESULT:\n{result}")
                return
            except json.JSONDecodeError:
                print("Error extracting arguments on Fast Path. Falling back...")

        # --- SLOW PATH: First time seeing this intent ---
        print("☁️ SLOW PATH: Unknown intent. Letting the ReAct Agent decide...")
        
        # Let the agent figure out what to do step-by-step
        response = await agent.achat(query)
        print(f"✅ AGENT ANSWER:\n{response.response}")
        
        # --- THE MAGIC: Cache the Agent's Decision ---
        # LlamaIndex stores every tool it used inside `response.sources`
        if response.sources:
            # Grab the name of the first tool the agent successfully used
            used_tool_name = response.sources[0].tool_name
            
            print(f"🧠 LEARNING: Caching '{used_tool_name}' for future use.")
            
            # Save the relationship (User Query -> Tool Name) to Redis
            redis_cache.store(prompt=query, response=used_tool_name)
        else:
            print("No tools were used (standard conversation). Nothing to route.")

    # --- Test 1: The First Execution (Slow Path) ---
    # The system has never seen this before. It will run the full ReAct agent,
    # figure out it needs `add_employee`, execute it, and then cache that decision.
    await execute_smart_query("Please add a new guy named John to the Sales team with a 50000 salary.")

    # --- Test 2: A Similar Execution (Fast Path) ---
    # The intent is the same, but the data is different.
    # Redis will intercept this, instantly load `add_employee`, and skip the ReAct loop entirely!
    await execute_smart_query("We need to hire Sarah for the HR department. Her salary is 60000.")

if __name__ == "__main__":
    asyncio.run(main())

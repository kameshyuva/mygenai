import asyncio
import json
from typing import List

from llama_index.core import VectorStoreIndex, Document, Settings
from llama_index.core.agent import FunctionAgent
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.tools.mcp import BasicMCPClient, McpToolSpec
from llama_index.vector_stores.redis import RedisVectorStore

# RedisVL Integrations
from redisvl.schema import IndexSchema
from redisvl.extensions.llmcache import SemanticCache

async def execute_semantically_routed_query(query: str):
    # 1. Initialize Local LLM and Embeddings
    llm = Ollama(model="llama3.1", request_timeout=120.0)
    embed_model = OllamaEmbedding(model="nomic-embed-text")
    
    Settings.llm = llm
    Settings.embed_model = embed_model
    
    query_embedding = embed_model.get_text_embedding(query)

    # 2. Extract Tools via MCP First
    # We must do this before the cache check because the agent will need 
    # the actual tool objects regardless of whether it's a cache hit or miss.
    mcp_client = BasicMCPClient("python", args=["path/to/your/mcp_server.py"])
    mcp_tool_spec = McpToolSpec(client=mcp_client)
    all_llama_tools = mcp_tool_spec.to_tool_list()
    
    if not all_llama_tools:
        print("No tools found on the MCP server.")
        return

    tool_mapping = {tool.metadata.name: tool for tool in all_llama_tools}

    # 3. Initialize RedisVL Semantic Cache for Tool Routing
    routing_cache = SemanticCache(
        name="mcp_tool_route_cache",
        redis_url="redis://localhost:6379",
        distance_threshold=0.15
    )
    
    # 4. Check Cache for Previous Routing Decisions
    cached_routes = routing_cache.check(vector=query_embedding)
    
    if cached_routes:
        print("⚡ Routing Cache Hit! Loading previously selected tools.")
        # Deserialize the stored JSON list of tool names
        routed_tool_names = json.loads(cached_routes[0]["response"])
    else:
        print("⏳ Routing Cache Miss. Performing semantic search for tools...")
        
        # Prepare Tool Documents
        routing_documents = [
            Document(
                text=f"Tool Name: {tool.metadata.name}\nDescription: {tool.metadata.description}",
                metadata={"tool_name": tool.metadata.name}
            ) for tool in all_llama_tools
        ]

        # Configure Vector Store for Tool Routing
        custom_schema = IndexSchema.from_dict({
            "index": {"name": "mcp-semantic-router", "prefix": "mcp_tool"},
            "fields": [
                {"name": "tool_name", "type": "tag"},
                {"name": "text", "type": "text"},
                {
                    "name": "vector",
                    "type": "vector",
                    "attrs": {
                        "dims": 768, 
                        "distance_metric": "cosine",
                        "algorithm": "flat",
                        "datatype": "float32"
                    }
                }
            ]
        })

        vector_store = RedisVectorStore(
            schema=custom_schema,
            redis_url="redis://localhost:6379",
            overwrite=True 
        )
        
        # Semantic Routing
        index = VectorStoreIndex.from_documents(
            routing_documents, 
            vector_store=vector_store
        )
        
        retriever = index.as_retriever(similarity_top_k=2)
        retrieved_nodes = retriever.retrieve(query) 
        
        routed_tool_names = [node.metadata["tool_name"] for node in retrieved_nodes]
        
        # Store the routing decision in the cache as a JSON string
        print("💾 Storing routing decision in Semantic Cache...")
        routing_cache.store(
            prompt=query,
            response=json.dumps(routed_tool_names),
            vector=query_embedding
        )

    print(f"Executing Agent with tools: {routed_tool_names}")
    routed_tools = [tool_mapping[name] for name in routed_tool_names]

    # 5. Execute with FunctionAgent (Fresh generation every time, no guardrails)
    agent = FunctionAgent.from_tools(
        tools=routed_tools,
        llm=llm,
        verbose=True
    )
    
    response = await agent.achat(query)
    return str(response)

# Example execution
if __name__ == "__main__":
    # Run 1: Cache Miss. Embeds all tools, searches vector DB, caches ["sales_data_tool"], executes agent.
    query = "Look up the latest sales data and format it into a summary report."
    result1 = asyncio.run(execute_semantically_routed_query(query))
    print(f"\nResult 1:\n{result1}\n")
    
    # Run 2: Cache Hit. Bypasses vector DB search, loads ["sales_data_tool"] directly, executes agent for fresh data.
    similar_query = "Fetch the recent sales data and give me a summary."
    result2 = asyncio.run(execute_semantically_routed_query(similar_query))
    print(f"\nResult 2:\n{result2}\n")

import asyncio
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

    # 2. Initialize RedisVL Semantic Cache
    # distance_threshold determines how similar a query must be to trigger a cache hit.
    # Lower is stricter (e.g., 0.1), higher is looser (e.g., 0.25).
    llmcache = SemanticCache(
        name="mcp_agent_cache",
        redis_url="redis://localhost:6379",
        distance_threshold=0.15
    )
    
    # 3. Check Cache First
    cached_responses = llmcache.check(vector=query_embedding)
    
    if cached_responses:
        print("⚡ Cache Hit! Returning stored response.")
        return cached_responses[0]["response"]
        
    print("⏳ Cache Miss. Proceeding to Semantic Routing and Agent Execution...")

    # 4. Extract Tools via MCP
    mcp_client = BasicMCPClient("python", args=["path/to/your/mcp_server.py"])
    mcp_tool_spec = McpToolSpec(client=mcp_client)
    all_llama_tools = mcp_tool_spec.to_tool_list()
    
    if not all_llama_tools:
        print("No tools found on the MCP server.")
        return

    # 5. Prepare Tool Documents
    tool_mapping = {tool.metadata.name: tool for tool in all_llama_tools}
    routing_documents = [
        Document(
            text=f"Tool Name: {tool.metadata.name}\nDescription: {tool.metadata.description}",
            metadata={"tool_name": tool.metadata.name}
        ) for tool in all_llama_tools
    ]

    # 6. Configure Vector Store for Tool Routing
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
    
    # 7. Semantic Routing
    index = VectorStoreIndex.from_documents(
        routing_documents, 
        vector_store=vector_store
    )
    
    retriever = index.as_retriever(similarity_top_k=2)
    
    # We can pass the query string here since LlamaIndex handles the embedding internally for the retriever
    retrieved_nodes = retriever.retrieve(query) 
    
    routed_tool_names = [node.metadata["tool_name"] for node in retrieved_nodes]
    routed_tools = [tool_mapping[name] for name in routed_tool_names]
    
    print(f"Semantically routed to tools: {routed_tool_names}")

    # 8. Execute with FunctionAgent (No Guardrails)
    agent = FunctionAgent.from_tools(
        tools=routed_tools,
        llm=llm,
        verbose=True
    )
    
    response = await agent.achat(query)
    response_text = str(response)

    # 9. Store the New Query and Result in Cache
    print("💾 Storing query and response in Semantic Cache...")
    llmcache.store(
        prompt=query,
        response=response_text,
        vector=query_embedding
    )

    return response_text

# Example execution
if __name__ == "__main__":
    # Run 1: Should be a Cache Miss, execute MCP tools, and store the result.
    query = "Look up the latest sales data and format it into a summary report."
    result1 = asyncio.run(execute_semantically_routed_query(query))
    print(f"\nResult 1:\n{result1}\n")
    
    # Run 2: Should be a Cache Hit and return instantly.
    similar_query = "Fetch the recent sales data and give me a summary."
    result2 = asyncio.run(execute_semantically_routed_query(similar_query))
    print(f"\nResult 2:\n{result2}\n")

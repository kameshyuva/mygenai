from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.core.objects import ObjectIndex, SimpleToolNodeMapping
from llama_index.core import VectorStoreIndex
from llama_index.tools.mcp import BasicMCPClient, McpToolSpec

class MCPToolRetrieverManager:
    def __init__(self, mcp_server_url: str, similarity_top_k: int = 3):
        self.mcp_url = mcp_server_url
        self.top_k = similarity_top_k
        
        # Initialize Nomic via your local Ollama instance
        self.embed_model = OllamaEmbedding(
            model_name="nomic-embed-text",
            base_url="http://localhost:11434", # Standard Ollama port
            ollama_additional_kwargs={"num_thread": 8} # Match your 8-core CPU
        )
        
        self.client = BasicMCPClient(self.mcp_url)
        self.tool_spec = McpToolSpec(client=self.client)
        self.object_index = None

    async def initialize(self):
        # Fetch tools from your MCP server
        tools = await self.tool_spec.to_tool_list_async()
        
        # Map tools to vector nodes
        tool_mapping = SimpleToolNodeMapping.from_objects(tools)
        
        # Create the searchable index using Nomic
        self.object_index = ObjectIndex.from_objects(
            tools,
            index_cls=VectorStoreIndex,
            object_mapping=tool_mapping,
            embed_model=self.embed_model
        )
        print(f"Indexed {len(tools)} MCP tools using nomic-embed-text.")

    def get_retriever(self):
        return self.object_index.as_retriever(similarity_top_k=self.top_k)

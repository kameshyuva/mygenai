from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.core.objects import ObjectIndex, SimpleToolNodeMapping
from llama_index.core import VectorStoreIndex
from llama_index.core.postprocessor import SimilarityPostprocessor
from llama_index.tools.mcp import BasicMCPClient, McpToolSpec

class MCPToolRetrieverManager:
    def __init__(self, mcp_server_url: str, similarity_top_k: int = 3):
        self.mcp_url = mcp_server_url
        self.top_k = similarity_top_k
        
        # FIX 1: Nomic Prefixes are REQUIRED for relevance
        self.embed_model = OllamaEmbedding(
            model_name="nomic-embed-text",
            query_prefix="search_query: ",
            text_prefix="search_document: ",
            ollama_additional_kwargs={"num_thread": 8}
        )
        
        self.client = BasicMCPClient(self.mcp_url)
        self.tool_spec = McpToolSpec(client=self.client)
        self.object_index = None

    async def initialize(self):
        # Using the tool list from your MCP client
        tools = await self.tool_spec.to_tool_list_async()
        
        # Map tools to nodes
        tool_mapping = SimpleToolNodeMapping.from_objects(tools)
        
        # FIX 2: Use the factory method .from_objects()
        # This internally handles the 'nodes' and 'VectorStoreIndex' setup
        self.object_index = ObjectIndex.from_objects(
            tools,
            index_cls=VectorStoreIndex,
            object_mapping=tool_mapping,
            embed_model=self.embed_model
        )
        print(f"Indexed {len(tools)} tools with Nomic prefixes.")

    def get_retriever(self):
        if not self.object_index:
            raise ValueError("Index not initialized.")
            
        # FIX 3: Add a similarity bouncer to stop 'random' low-quality matches
        # 0.6 is a safe starting threshold for Nomic
        bouncer = SimilarityPostprocessor(similarity_cutoff=0.6)
        
        return self.object_index.as_retriever(
            similarity_top_k=self.top_k,
            node_postprocessors=[bouncer]
        )

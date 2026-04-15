from llama_index.core import VectorStoreIndex
from llama_index.core.objects import ObjectIndex, SimpleToolNodeMapping
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.core.postprocessor import SimilarityPostprocessor
from llama_index.tools.mcp import BasicMCPClient, McpToolSpec

class MCPToolRetrieverManager:
    def __init__(self, mcp_server_url: str, similarity_top_k: int = 3):
        self.mcp_url = mcp_server_url
        self.top_k = similarity_top_k
        
        # Nomic Prefixes: Essential for matching query intent to tool docs
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
        # 1. Fetch raw tools from MCP
        tools = await self.tool_spec.to_tool_list_async()
        
        # 2. Create the mapping (this links Node IDs to Python Objects)
        tool_mapping = SimpleToolNodeMapping.from_objects(tools)
        
        # 3. WEIGTED APPROACH: Create and modify nodes manually
        # This converts tools into searchable nodes
        nodes = tool_mapping.to_nodes(tools)
        
        for node in nodes:
            # We recover the tool name from the mapping's internal logic 
            # and prepend it to the text 3 times to 'anchor' the vector.
            tool_name = node.metadata.get("name", "unknown_tool")
            original_desc = node.text
            
            # Weighted String: "TOOL: infra_check TOOL: infra_check ... [description]"
            node.text = f"TOOL: {tool_name} " * 3 + f"\nDESCRIPTION: {original_desc}"

        # 4. Build the index from our modified nodes
        vector_index = VectorStoreIndex(
            nodes, 
            embed_model=self.embed_model
        )
        
        # 5. Connect the VectorIndex to the ObjectIndex manually
        # This is the correct __init__ pattern
        self.object_index = ObjectIndex(
            index=vector_index, 
            object_mapping=tool_mapping
        )
        
        print(f"Successfully built weighted index for {len(tools)} tools.")

    def get_retriever(self):
        if not self.object_index:
            raise ValueError("Index not initialized.")
            
        # The similarity cutoff ensures 'random' tools are dropped
        bouncer = SimilarityPostprocessor(similarity_cutoff=0.6)
        
        return self.object_index.as_retriever(
            similarity_top_k=self.top_k,
            node_postprocessors=[bouncer]
        )

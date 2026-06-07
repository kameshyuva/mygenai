import httpx
from typing import List
from contextvars import ContextVar
from llama_index.core import VectorStoreIndex
from llama_index.core.objects import ObjectIndex, SimpleToolNodeMapping
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.core.postprocessor import SimilarityPostprocessor
from llama_index.tools.mcp import BasicMCPClient, McpToolSpec

# Thread-safe context variables mapped to your FastAPI middleware
current_user_realm: ContextVar[str] = ContextVar("current_user_realm", default="system")
current_user_token: ContextVar[str] = ContextVar("current_user_token", default="")

class MultiTenantMCPManager:
    def __init__(self, mcp_server_url: str, similarity_top_k: int = 2):
        self.mcp_url = mcp_server_url
        self.top_k = similarity_top_k
        
        # 1. Setup the HTTPX Client with an Auth hook for live injection
        class LiveHeaderInjector(httpx.Auth):
            def auth_flow(self, request):
                # This code executes the millisecond an agent fires a tool call
                realm = current_user_realm.get()
                token = current_user_token.get()
                
                request.headers["X-User-Realm"] = realm
                if token:
                    request.headers["Authorization"] = f"Bearer {token}"
                yield request

        self.http_client = httpx.AsyncClient(
            auth=LiveHeaderInjector(),
            timeout=60.0
        )
        
        # 2. Pass the dynamic HTTPX instance to the LlamaIndex Client
        self.client = BasicMCPClient(
            command_or_url=self.mcp_url,
            http_client=self.http_client
        )
        
        self.tool_spec = McpToolSpec(client=self.client)
        self.embed_model = OllamaEmbedding(
            model_name="nomic-embed-text",
            query_prefix="search_query: ",
            text_prefix="search_document: ",
            ollama_additional_kwargs={"num_thread": 4}
        )
        self._object_index = None
        self._is_initialized = False

    async def initialize_once(self, system_token: str = "init_token"):
        """
        Runs EXACTLY ONCE at application boot time.
        Uses system context variables to pass the initial structural scan handshake.
        """
        if self._is_initialized:
            return

        # Temporarily set system tokens to fetch tool list metadata schemas
        token_token = current_user_token.set(system_token)
        realm_token = current_user_realm.set("system_bootstrap")
        
        try:
            raw_tools = await self.tool_spec.to_tool_list_async()
            tool_mapping = SimpleToolNodeMapping.from_objects(raw_tools)
            nodes = tool_mapping.to_nodes(raw_tools)
            
            for node in nodes:
                name = node.metadata.get("name", "tool")
                node.text = f"TOOL: {name} " * 3 + f"\nDESCRIPTION: {node.text}"

            vector_index = VectorStoreIndex(nodes, embed_model=self.embed_model)
            self._object_index = ObjectIndex(index=vector_index, object_mapping=tool_mapping)
            self._is_initialized = True
            print("⚡ Global structural tool index generated using system metadata credentials.")
        finally:
            # Clean up the context variables immediately after bootstrap
            current_user_token.reset(token_token)
            current_user_realm.reset(realm_token)

    def get_retriever(self):
        if not self._is_initialized:
            raise RuntimeError("Manager must be initialized at app boot.")
        bouncer = SimilarityPostprocessor(similarity_cutoff=0.65)
        return self._object_index.as_retriever(
            similarity_top_k=self.top_k,
            node_postprocessors=[bouncer]
        )

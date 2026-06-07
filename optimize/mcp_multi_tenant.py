# mcpmanager.py
import httpx
import pandas as pd
from contextvars import ContextVar
from llama_index.core import VectorStoreIndex
from llama_index.core.objects import ObjectIndex, SimpleToolNodeMapping
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.core.postprocessor import SimilarityPostprocessor
from llama_index.tools.mcp import BasicMCPClient, McpToolSpec
from llama_index.core.tools import FunctionTool

# Thread-safe Context Variables shared across your async execution trees
current_user_realm: ContextVar[str] = ContextVar("current_user_realm", default="system_init")
current_user_token: ContextVar[str] = ContextVar("current_user_token", default="")

class MultiTenantMCPManager:
    def __init__(self, mcp_server_url: str, similarity_top_k: int = 3):
        self.mcp_url = mcp_server_url
        self.top_k = similarity_top_k
        
        # 1. Custom Auth Flow handles injection when a tool is triggered
        class LiveHeaderInjector(httpx.Auth):
            def auth_flow(self, request):
                # Reads current token values active on this asyncio Task
                realm = current_user_realm.get()
                token = current_user_token.get()
                
                request.headers["X-User-Realm"] = realm
                if token:
                    request.headers["Authorization"] = f"Bearer {token}"
                yield request

        # 2. Single persistent HTTP client prevents port exhaustion on your CPU stack
        self.http_client = httpx.AsyncClient(
            auth=LiveHeaderInjector(),
            timeout=60.0
        )
        
        self.client = BasicMCPClient(
            command_or_url=self.mcp_url,
            http_client=self.http_client
        )
        self.tool_spec = McpToolSpec(client=self.client)
        
        # 3. CPU Thread optimized embedding config for nomic
        self.embed_model = OllamaEmbedding(
            model_name="nomic-embed-text",
            query_prefix="search_query: ",
            text_prefix="search_document: ",
            ollama_additional_kwargs={"num_thread": 4},
            keep_alive="60m"
        )
        
        self._object_index = None
        self._is_initialized = False

    def _normalize_to_markdown(self, data) -> str:
        """Flattens nested JSON into a grid to prevent Qwen attention dilution."""
        try:
            if not data:
                return "NO DATA RETURNED"
            df = pd.json_normalize(data, sep='_')
            return df.to_markdown(index=False)
        except Exception:
            return f"DATA_RAW: {str(data)}"

    def _wrap_tool(self, tool: FunctionTool) -> FunctionTool:
        """Wraps async functions to auto-flatten complex multi-step dependency outputs."""
        original_async_fn = tool.async_fn
        
        async def wrapped_async_fn(*args, **kwargs):
            raw_result = await original_async_fn(*args, **kwargs)
            return self._normalize_to_markdown(raw_result)
        
        tool.async_fn = wrapped_async_fn
        return tool

    async def initialize_once(self, bootstrap_token: str = "init_token"):
        """Executes exactly once on application boot inside startup lifespans."""
        if self._is_initialized:
            return

        # Explicitly set system context parameters for the structural tool discovery loop
        t_token = current_user_token.set(bootstrap_token)
        r_token = current_user_realm.set("system_bootstrap")
        
        try:
            raw_tools = await self.tool_spec.to_tool_list_async()
            normalized_tools = [self._wrap_tool(t) for t in raw_tools]
            
            tool_mapping = SimpleToolNodeMapping.from_objects(normalized_tools)
            nodes = tool_mapping.to_nodes(normalized_tools)
            
            # Prepend names 3x to weight vectors over generic text strings
            for node in nodes:
                name = node.metadata.get("name", "tool")
                node.text = f"TOOL: {name} " * 3 + f"\nDESCRIPTION: {node.text}"

            vector_index = VectorStoreIndex(nodes, embed_model=self.embed_model)
            self._object_index = ObjectIndex(index=vector_index, object_mapping=tool_mapping)
            self._is_initialized = True
            print("⚡ MCP Tool Structure cached successfully in background memory.")
        finally:
            # Revert variables to protect context safety bounds
            current_user_token.reset(t_token)
            current_user_realm.reset(r_token)

    def get_retriever(self):
        if not self._is_initialized:
            raise RuntimeError("MCP Tool Cache has not been compiled.")
        bouncer = SimilarityPostprocessor(similarity_cutoff=0.65)
        return self._object_index.as_retriever(
            similarity_top_k=self.top_k,
            node_postprocessors=[bouncer]
        )

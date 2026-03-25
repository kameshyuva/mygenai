import chromadb
from llama_index.core.memory import (
    Memory,
    StaticMemoryBlock,         # NEW: Added for identity anchoring
    FactExtractionMemoryBlock,
    VectorMemoryBlock
)
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.llms.ollama import Ollama

class AdvancedAgentMemory:
    def __init__(
        self,
        agent_id: str,          # NEW: Unique ID for the agent (e.g., "researcher_01")
        agent_persona: str,     # NEW: Core identity/role description
        collection_name: str = "shared_project_context",
        host: str = "localhost",
        port: int = 8000
    ):
        self.agent_id = agent_id

        # 1. Static Identity Block (Priority 0 - Highest)
        # This anchors the agent so it doesn't get confused by the shared vector memory.
        # It is always injected at the very top of the LLM prompt.
        self.identity_block = StaticMemoryBlock(
            name=f"identity_{agent_id}",
            static_content=f"System Role: You are {agent_id}. {agent_persona}",
            priority=0 
        )

        # 2. Fact Extraction Block (Priority 1 - Isolated per instance)
        # Qwen3.5 will only extract facts from THIS agent's active Short-Term Memory
        self.extraction_llm = Ollama(model="qwen3.5", temperature=0.1, request_timeout=120.0)
        self.fact_block = FactExtractionMemoryBlock(
            llm=self.extraction_llm,
            max_facts=50,
            priority=1 
        )

        # 3. Vector Memory Block (Priority 2 - Shared)
        # Points to the central ChromaDB server so all agents can read/write to the same pool
        self.db_client = chromadb.HttpClient(host=host, port=port)
        self.chroma_collection = self.db_client.get_or_create_collection(collection_name)
        self.vector_store = ChromaVectorStore(chroma_collection=self.chroma_collection)
        
        self.vector_block = VectorMemoryBlock(
            vector_store=self.vector_store,
            embed_model=OllamaEmbedding(model_name="nomic-embed-text"),
            priority=2 
        )

    def get_memory(self) -> Memory:
        return Memory(
            token_limit=3000,
            chat_history_token_ratio=0.7,
            # Note the inclusion of the identity block at the front of the list
            memory_blocks=[self.identity_block, self.fact_block, self.vector_block]
        )

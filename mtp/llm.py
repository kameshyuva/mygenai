# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "llama-index-core",
#   "llama-index-llms-ollama",
#   "llama-index-embeddings-ollama",
#   "llama-index-llms-openai-like",
#   "llama-index-embeddings-openai"
# ]
# ///

from typing import Protocol
from llama_index.core.llms import LLM
from llama_index.core.embeddings import BaseEmbedding

from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.llms.openai_like import OpenAILike
from llama_index.embeddings.openai import OpenAIEmbedding

# =====================================================================
# 1. Structural Interface Protocol
# =====================================================================
class ModelProvider(Protocol):
    """
    A strict interface contract for local model infrastructure providers.
    Enforces independent retrieval methods for LLMs and Embedding engines.
    """
    
    def get_llm(self) -> LLM:
        """Returns the primary text generation / chat LLM instance."""
        ...

    def get_embedding(self) -> BaseEmbedding:
        """Returns the text embedding model instance."""
        ...


# =====================================================================
# 2. Ollama Implementation
# =====================================================================
class OllamaProvider:
    """
    Concrete implementation of ModelProvider utilizing an Ollama backend.
    Optimized for fast utility tasks like summarization, extraction, and light embedding.
    """
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url

    def get_llm(self) -> LLM:
        return Ollama(
            base_url=self.base_url,
            model="llama3.2:3b",
            request_timeout=60.0
        )

    def get_embedding(self) -> BaseEmbedding:
        return OllamaEmbedding(
            base_url=self.base_url,
            model_name="nomic-embed-text"
        )


# =====================================================================
# 3. Llama.cpp (OpenAILike) Implementation
# =====================================================================
class LlamaCppProvider:
    """
    Concrete implementation of ModelProvider utilizing OpenAI-compatible llama.cpp servers.
    Optimized for heavy agentic workloads leveraging Multi-Token Prediction (MTP).
    """
    def __init__(
        self, 
        chat_url: str = "http://localhost:11436/v1", 
        embed_url: str = "http://localhost:11435/v1"
    ):
        self.chat_url = chat_url
        self.embed_url = embed_url

    def get_llm(self) -> LLM:
        return OpenAILike(
            api_base=self.chat_url,
            api_key="airgapped-key",
            model="gemma-4",
            is_chat_model=True,
            is_function_calling_model=True,
            timeout=120.0,
            additional_kwargs={
                "seed": 42,
                "extra_body": {
                    "min_p": 0.05,
                    "repeat_penalty": 1.15
                }
            }
        )

    def get_embedding(self) -> BaseEmbedding:
        return OpenAIEmbedding(
            api_base=self.embed_url,
            api_key="airgapped-key",
            model_name="nomic-embed-text"
        )


# =====================================================================
# Example Verification / Usage Loop
# =====================================================================
if __name__ == "__main__":
    from llama_index.core import Settings
    
    print("Testing structural subtyping validation...")
    
    # Instantiate the concrete objects
    ollama_infra: ModelProvider = OllamaProvider()
    llamacpp_infra: ModelProvider = LlamaCppProvider()
    
    # 1. Setup baseline orchestration via Ollama
    Settings.llm = ollama_infra.get_llm()
    Settings.embed_model = ollama_infra.get_embedding()
    print(f"-> Global Context configured with: {type(Settings.llm).__name__}")
    
    # 2. Extract high-performance reasoning core for your execution loop
    agent_reasoning_engine = llamacpp_infra.get_llm()
    print(f"-> Core Agent Worker initialized with: {type(agent_reasoning_engine).__name__}")
    
    print("\nProtocol implementations validated successfully.")

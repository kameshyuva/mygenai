import json
import os
from typing import Protocol, List

import redis
import chromadb

# LlamaIndex Imports
from llama_index.core.vector_stores.types import BaseVectorStore
from llama_index.core.storage.chat_store import BaseChatStore, SimpleChatStore
from llama_index.storage.chat_store.redis import RedisChatStore
from llama_index.vector_stores.redis import RedisVectorStore
from llama_index.vector_stores.chroma import ChromaVectorStore

# RedisVL Import for the new Schema requirement
from redisvl.schema import IndexSchema


class StorageProvider(Protocol):
    """
    Protocol defining the required interface for storage backends.
    Any new database must implement these 4 methods.
    """
    def get_vector_store(self) -> BaseVectorStore:
        ...

    def get_chat_store(self) -> BaseChatStore:
        ...

    def save_facts(self, session_id: str, facts: List[str]) -> None:
        ...

    def load_facts(self, session_id: str) -> List[str]:
        ...


class RedisStorageProvider:
    """
    Implementation using Redis for Vectors, Chat History, and Facts.
    """
    def __init__(self, redis_url: str = "redis://localhost:6379", embed_dims: int = 768):
        self.redis_url = redis_url
        self.client = redis.Redis.from_url(redis_url)
        
        # In the latest versions, RedisVectorStore strictly requires an IndexSchema.
        # This explicitly maps the fields LlamaIndex expects to the underlying Redis database.
        self.schema = IndexSchema.from_dict({
            "index": {
                "name": "agent_vector_history",
                "prefix": "vector_docs"
            },
            "fields": [
                # Required LlamaIndex tracking fields
                {"type": "tag", "name": "id"},
                {"type": "tag", "name": "doc_id"},
                {"type": "text", "name": "text"},
                # Vector field definition
                {
                    "type": "vector",
                    "name": "vector",
                    "attrs": {
                        # Make sure this matches your embedding model (e.g., 768 for nomic-embed-text)
                        "dims": embed_dims,  
                        "algorithm": "hnsw",
                        "distance_metric": "cosine"
                    }
                }
            ]
        })

    def get_vector_store(self) -> BaseVectorStore:
        return RedisVectorStore(
            schema=self.schema,
            redis_url=self.redis_url, 
            overwrite=False
        )

    def get_chat_store(self) -> BaseChatStore:
        return RedisChatStore(redis_url=self.redis_url)

    def save_facts(self, session_id: str, facts: List[str]) -> None:
        self.client.set(f"facts_{session_id}", json.dumps(facts))

    def load_facts(self, session_id: str) -> List[str]:
        raw = self.client.get(f"facts_{session_id}")
        return json.loads(raw) if raw else []


class ChromaStorageProvider:
    """
    Implementation using a separate Chroma instance via HTTP.
    Facts and Chat History remain local (SimpleChatStore/File) as Chroma is vector-only.
    """
    def __init__(self, host: str = "localhost", port: int = 8000, facts_dir: str = "./facts"):
        self.facts_dir = facts_dir
        os.makedirs(self.facts_dir, exist_ok=True)
        
        # Connect to the external Chroma instance via HTTP
        self.chroma_client = chromadb.HttpClient(host=host, port=port)

    def get_vector_store(self) -> BaseVectorStore:
        # Note: If the server is just starting, it might take a moment to be ready
        chroma_collection = self.chroma_client.get_or_create_collection("agent_vector_history")
        return ChromaVectorStore(chroma_collection=chroma_collection)

    def get_chat_store(self) -> BaseChatStore:
        # Chroma is vector-only; Short-term history stays in RAM
        return SimpleChatStore()

    def save_facts(self, session_id: str, facts: List[str]) -> None:
        file_path = os.path.join(self.facts_dir, f"{session_id}.json")
        with open(file_path, "w") as f:
            json.dump(facts, f)

    def load_facts(self, session_id: str) -> List[str]:
        file_path = os.path.join(self.facts_dir, f"{session_id}.json")
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                return json.load(f)
        return []

from llama_index.vector_stores.redis import RedisVectorStore
from llama_index.storage.kvstore.redis import RedisKVStore
from llama_index.core.storage import StorageContext
from llama_index.core.storage.docstore import KVDocumentStore

def get_redis_storage_context(redis_url: str = "redis://localhost:6379") -> StorageContext:
    """
    Configures Redis as the unified backend for both Vector Storage and Key-Value Storage.
    """
    # Configure Redis for Vectors
    vector_store = RedisVectorStore(
        redis_url=redis_url,
        index_name="agent_vector_history",
        overwrite=False
    )

    # Configure Redis for Key-Value/Documents
    kv_store = RedisKVStore(redis_url=redis_url)
    doc_store = KVDocumentStore(kv_store)

    # Create and return the unified Storage Context
    storage_context = StorageContext.from_defaults(
        vector_store=vector_store,
        docstore=doc_store,
    )
    
    return storage_context

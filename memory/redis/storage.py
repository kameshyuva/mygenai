import redis
from llama_index.vector_stores.redis import RedisVectorStore
from llama_index.storage.chat_store.redis import RedisChatStore

REDIS_URL = "redis://localhost:6379"

def get_redis_vector_store():
    # VectorMemoryBlock needs this directly
    return RedisVectorStore(
        redis_url=REDIS_URL,
        index_name="agent_vector_history",
        overwrite=False
    )

def get_redis_chat_store():
    # If you want persistent Short-Term Memory, use this. 
    # If not, you can just use SimpleChatStore() in agent.py
    return RedisChatStore(redis_url=REDIS_URL)

def get_raw_redis_client():
    # For manually saving/loading Facts in the wrapper
    return redis.Redis.from_url(REDIS_URL)

from llama_index.core.agent import FunctionAgent
from llama_index.core.memory.blocks import FactExtractionMemoryBlock, VectorMemoryBlock
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.storage.chat_store.redis import RedisChatStore
from llama_index.llms.ollama import Ollama

from storage import get_redis_storage_context
from memory_wrapper import AsyncRedisAgentMemory

def create_agent(session_id: str = "user_session_1") -> FunctionAgent:
    main_llm = Ollama(model="llama3", request_timeout=120.0)
    extraction_llm = Ollama(model="qwen3.5:0.5b", request_timeout=60.0)

    storage_context = get_redis_storage_context()

    # 1. Initialize Heavy Blocks
    fact_block = FactExtractionMemoryBlock(
        llm=extraction_llm,
        storage_context=storage_context
    )
    vector_block = VectorMemoryBlock(
        storage_context=storage_context
    )

    # 2. Setup pure Redis Chat Store
    chat_store = RedisChatStore(redis_url="redis://localhost:6379")

    # 3. Create the Short-Term Buffer using Redis
    # This handles token truncation perfectly, so no SQLite is needed.
    redis_stm_buffer = ChatMemoryBuffer.from_defaults(
        chat_store=chat_store,
        chat_store_key=session_id,
        token_limit=4000
    )

    # 4. Wrap everything in our custom Async Redis Manager
    agent_memory = AsyncRedisAgentMemory(
        stm_buffer=redis_stm_buffer,
        memory_blocks=[fact_block, vector_block]
    )
    
    # 5. Build Agent
    agent = FunctionAgent(
        llm=main_llm,
        memory=agent_memory,
    )
    
    return agent

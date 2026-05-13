import asyncio
from llama_index.core.agent import FunctionAgent
from llama_index.core.memory.blocks import FactExtractionMemoryBlock, VectorMemoryBlock
from llama_index.llms.ollama import Ollama

from storage import get_redis_storage_context
from memory_wrapper import AsyncBackgroundMemory

def create_agent(session_id: str = "user_session_1") -> FunctionAgent:
    main_llm = Ollama(model="llama3", request_timeout=120.0)
    extraction_llm = Ollama(model="qwen3.5:0.5b", request_timeout=60.0)

    # Redis is now strictly used for your Heavy Blocks (LTM)
    storage_context = get_redis_storage_context()

    fact_block = FactExtractionMemoryBlock(
        llm=extraction_llm,
        storage_context=storage_context
    )
    vector_block = VectorMemoryBlock(
        storage_context=storage_context
    )

    # 1. Initialize modern Memory
    # It natively uses in-memory SQLite for the Short-Term queue
    agent_memory = AsyncBackgroundMemory.from_defaults(
        session_id=session_id,
        memory_blocks=[fact_block, vector_block],
        token_limit=4000
    )

    # 2. THE FIX: Force SQLite Table Creation
    # Calling the async get() method forces the internal SQL engine to execute 
    # the CREATE TABLE command before the agent starts executing synchronously.
    try:
        # If running in a normal Python script without an active event loop
        asyncio.run(agent_memory.aget())
    except RuntimeError:
        # If an event loop is already running (e.g. FastAPI), you can safely ignore this.
        # The first async request to the agent will naturally create the table.
        pass

    # 3. Build Agent
    agent = FunctionAgent(
        llm=main_llm,
        memory=agent_memory,
    )
    
    return agent

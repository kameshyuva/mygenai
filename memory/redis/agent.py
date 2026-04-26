from llama_index.core.agent import FunctionAgent
from llama_index.core.memory import Memory
from llama_index.core.memory.blocks import SimpleMemoryBlock, FactExtractionMemoryBlock, VectorMemoryBlock
from llama_index.llms.ollama import Ollama

from storage import get_redis_storage_context
from memory_wrapper import ThreadedBackgroundMemory

def create_agent() -> FunctionAgent:
    """
    Assembles the FunctionAgent with layered memory architecture.
    """
    # 1. Setup Models
    # Main routing/reasoning model
    main_llm = Ollama(model="llama3", request_timeout=120.0)
    
    # Lightweight extraction model
    extraction_llm = Ollama(model="qwen3.5:0.5b", request_timeout=60.0)

    # 2. Setup unified Redis storage
    storage_context = get_redis_storage_context()

    # 3. Initialize heavy memory blocks using Redis
    fact_block = FactExtractionMemoryBlock(
        llm=extraction_llm,
        storage_context=storage_context
    )

    vector_block = VectorMemoryBlock(
        storage_context=storage_context
    )

    # 4. Wrap heavy blocks in the Threaded Memory wrapper
    background_heavy_memory = ThreadedBackgroundMemory(
        memory_blocks=[fact_block, vector_block],
        max_workers=1
    )

    # 5. Create the fast, synchronous short-term memory block
    short_term_memory = SimpleMemoryBlock()

    # 6. Combine into the final Agent Memory
    agent_memory = Memory(
        memory_blocks=[
            short_term_memory,      # Instant sync read/write
            background_heavy_memory # Instant sync read, async threaded write
        ]
    )

    # 7. Build and return the Agent
    agent = FunctionAgent(
        llm=main_llm,
        memory=agent_memory,
        # tools=[... your tools here ...]
    )
    
    return agent

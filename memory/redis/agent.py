import json
from llama_index.core.agent import FunctionAgent
from llama_index.core.memory.blocks import FactExtractionMemoryBlock, VectorMemoryBlock
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.llms.ollama import Ollama

from storage import get_redis_vector_store, get_redis_chat_store, get_raw_redis_client
from memory_wrapper import AsyncBackgroundMemory

def create_agent(session_id: str = "user_session_1") -> FunctionAgent:
    main_llm = Ollama(model="llama3", request_timeout=120.0)
    extraction_llm = Ollama(model="qwen3.5:0.5b", request_timeout=60.0)
    embed_model = OllamaEmbedding(model="nomic-embed-text") 

    # 1. Setup Vector Block
    vector_block = VectorMemoryBlock(
        vector_store=get_redis_vector_store(),
        embed_model=embed_model
    )

    # 2. Setup Fact Block + Load Saved Facts
    r_client = get_raw_redis_client()
    saved_facts_raw = r_client.get(f"facts_{session_id}")
    
    fact_block = FactExtractionMemoryBlock(llm=extraction_llm)
    if saved_facts_raw:
        fact_block.facts = json.loads(saved_facts_raw)

    # 3. Initialize Modern Memory with Redis Chat Store
    agent_memory = AsyncBackgroundMemory(
        chat_store=get_redis_chat_store(), 
        chat_store_key=session_id,
        memory_blocks=[fact_block, vector_block],
    )

    return FunctionAgent(llm=main_llm, memory=agent_memory)

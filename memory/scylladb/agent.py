import concurrent.futures
from llama_index.llms.ollama import Ollama
from llama_index.core.agent import FunctionAgent
from llama_index.core.memory import (
    Memory, 
    ChatMemoryBlock, 
    FactExtractionMemoryBlock, 
    VectorMemoryBlock
)
from scylla_store import ScyllaTimeSeriesChatStore
from deferred_memory import BackgroundBlock

# 1. Initialize Local LLM (Ollama)
# Using qwen3.5:4b as discussed
llm = Ollama(model="qwen3.5:4b", request_timeout=120.0)

# 2. Setup Thread Pool for background memory tasks
# Using 2 workers to balance CPU load on an 8-core machine
executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)

# 3. Setup Persistence & Memory Blocks
scylla_store = ScyllaTimeSeriesChatStore(contact_points=["127.0.0.1"])

# Short-term history is synchronous so the next turn is always accurate
sync_chat_block = ChatMemoryBlock(
    chat_store=scylla_store, 
    chat_store_key="user_session_001"
)

# Fact and Vector blocks are backgrounded to prevent blocking .run()
bg_fact_block = BackgroundBlock(
    FactExtractionMemoryBlock(llm=llm), 
    executor
)
# Assuming a pre-defined vector_store instance
# bg_vector_block = BackgroundBlock(VectorMemoryBlock(vector_store=vs), executor)

# 4. Assemble modern Memory module
memory = Memory(blocks=[sync_chat_block, bg_fact_block])

# 5. Initialize Agent
agent = FunctionAgent(
    tools=[], # Add your business tools here
    llm=llm,
    memory=memory,
    verbose=True
)

if __name__ == "__main__":
    # The .run() call returns as soon as the agent finishes, 
    # while fact extraction continues in the background.
    response = agent.run("Remind me about the critical alerts from this morning.")
    print(f"Agent Response: {response}")

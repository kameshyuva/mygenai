from llama_index.core.agent import FunctionAgent
from llama_index.llms.ollama import Ollama

# 1. Setup your extraction LLM (e.g., lightweight model for facts)
extraction_llm = Ollama(model="qwen3.5:0.5b")

# 2. Initialize your heavy memory blocks
fact_block = FactExtractionMemoryBlock(llm=extraction_llm)
vector_block = VectorMemoryBlock()

# 3. Wrap blocks in the custom Threaded Memory
# max_workers=1 ensures memory updates process sequentially in the background
memory = ThreadedBackgroundMemory(
    memory_blocks=[fact_block, vector_block],
    max_workers=1 
)

# 4. Run the agent normally
agent = FunctionAgent(
    memory=memory,
    # ... your tools and main LLM setup
)

# The agent will retrieve history synchronously, generate the response, 
# and then instantly return. The Fact/Vector updates will process in the thread pool.
response = agent.run("What are the recommended actions for the recent database alert?")

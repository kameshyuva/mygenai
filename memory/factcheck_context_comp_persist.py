from llama_index.core.agent import FunctionAgent
from llama_index.core.memory import Memory, FactExtractionMemoryBlock
from llama_index.llms.ollama import Ollama
from llama_index.storage.chat_store.cassandra import CassandraChatStore
from cassandra.cluster import Cluster
# Import your ContextCompressor from the previous step
from context_compressor import ContextCompressor 

# ---------------------------------------------------------
# 1. Initialize Hardware-Aware Models
# ---------------------------------------------------------
llm_main = Ollama(model="qwen3.5:9b", request_timeout=120.0)
llm_fast = Ollama(model="qwen3.5:0.5b", request_timeout=30.0)

# ---------------------------------------------------------
# 2. Connect to ScyllaDB (Persistent Storage)
# ---------------------------------------------------------
# Connect to your local/network ScyllaDB cluster
scylla_cluster = Cluster(['127.0.0.1']) 
scylla_session = scylla_cluster.connect()

# Initialize the ChatStore using ScyllaDB
chat_store = CassandraChatStore(
    session=scylla_session,
    keyspace="agent_memory_keyspace",
    table_name="chat_history"
)

# ---------------------------------------------------------
# 3. Configure the Fact Extraction Block
# ---------------------------------------------------------
# This block uses the 0.5B model to silently extract state/facts 
# from the conversation and push them into the system prompt area.
fact_extractor = FactExtractionMemoryBlock(
    llm=llm_fast,  # Route extraction tasks to the lightweight model!
    priority=0     # Priority 0 guarantees facts are never truncated
)

# ---------------------------------------------------------
# 4. Initialize the Modern Memory Module
# ---------------------------------------------------------
user_session_id = "user_123_alert_session" # Typically passed in via your FastAPI request

agent_memory = Memory.from_defaults(
    chat_store=chat_store,
    session_id=user_session_id,
    memory_blocks=[fact_extractor],
    token_limit=2000, # Strict limit to protect CPU inference
    chat_history_token_ratio=0.7 # 70% short-term conversation, 30% facts/long-term
)

# ---------------------------------------------------------
# 5. Bind to FunctionAgent
# ---------------------------------------------------------
agent = FunctionAgent.from_tools(
    tools=[], # Your MCP tools here 
    llm=llm_main,
    memory=agent_memory,
    system_prompt="You are a secure system agent designed for business alert assessment."
)

# Initialize the custom token-reduction compressor we built earlier
compressor = ContextCompressor(summary_model_name="qwen3.5:0.5b", max_tokens=1500)

# ---------------------------------------------------------
# 6. Execution Loop (FastAPI Endpoint Logic)
# ---------------------------------------------------------
def process_user_message(query: str):
    # Step 1: Garbage Collection. Squash old conversation to save compute.
    # (Leaves the FactExtractionMemoryBlock and System Prompt untouched)
    compressor.compress_memory_if_needed(agent.memory)
    
    # Step 2: Main Execution
    # Behind the scenes:
    # A) 9B model generates the response using the compressed context + extracted facts
    # B) 0.5B model (via FactExtractionMemoryBlock) silently parses the new interaction for new facts
    # C) CassandraChatStore asynchronously writes the new state to ScyllaDB
    response = agent.chat(query)
    
    return response.response

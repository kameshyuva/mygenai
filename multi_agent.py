from llama_index.core.agent import ReActAgent
from llama_index.llms.ollama import Ollama
from memory_manager import AdvancedAgentMemory

agent_llm = Ollama(model="llama3", temperature=0.4)

# --- Initialize Agent 1 ---
research_memory = AdvancedAgentMemory(
    agent_id="Research_Agent",
    agent_persona="You are responsible for gathering requirements and summarizing data. Do not write code."
)
research_agent = ReActAgent.from_tools(
    tools=[], 
    llm=agent_llm, 
    memory=research_memory.get_memory()
)

# --- Initialize Agent 2 ---
coding_memory = AdvancedAgentMemory(
    agent_id="Coding_Agent",
    agent_persona="You are responsible for writing Python code based on research summaries."
)
coding_agent = ReActAgent.from_tools(
    tools=[], 
    llm=agent_llm, 
    memory=coding_memory.get_memory()
)

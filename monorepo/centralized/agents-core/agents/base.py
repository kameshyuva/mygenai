from llama_index.core.agent import FunctionAgent
from llama_index.core.memory import SummaryMemory
from core.llm import get_default_llm

def build_agent(session_id: str) -> FunctionAgent:
    """
    Factory function to assemble the LlamaIndex agent.
    """
    llm = get_default_llm()
    
    # Utilizing modern memory modules to handle context pruning automatically
    memory = SummaryMemory(llm=llm)
    
    # State would be hydrated here using the session_id to pull from your database
    
    agent = FunctionAgent.from_tools(
        tools=[],  # Specific agent tools are injected here
        llm=llm,
        memory=memory,
        system_prompt=(
            "You are a highly capable analytical agent. "
            "Execute your tools sequentially and return flattened CSV data when possible."
        )
    )
    
    return agent

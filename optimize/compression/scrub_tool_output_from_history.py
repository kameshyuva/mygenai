from llama_index.core.memory import Memory
from llama_index.core.llms import MessageRole

def scrub_tool_payloads(memory: Memory) -> None:
    """
    Cleans the active memory buffer by removing intermediate tool executions.
    
    This filters out:
    1. The raw payload returned by the tools (MessageRole.TOOL).
    2. The LLM's internal request to trigger the tools (MessageRole.ASSISTANT with 'tool_calls').
    
    Leaves intact: System prompts, User prompts, and final Synthesized Assistant responses.
    """
    history = memory.get()
    
    lean_history = [
        msg for msg in history
        if msg.role != MessageRole.TOOL and 
        not (msg.role == MessageRole.ASSISTANT and "tool_calls" in msg.additional_kwargs)
    ]
    
    memory.set(lean_history)

from llama_index.core.memory import Memory
from llama_index.core.llms import ChatMessage, MessageRole

def prune_memory_for_execution(raw_memory_state: Memory) -> list[ChatMessage]:
    messages = raw_memory_state.get()
    
    if len(messages) <= 5: 
        return messages
        
    pruned_messages = []
    
    # 1. Always keep the system prompt
    if messages[0].role == MessageRole.SYSTEM:
        pruned_messages.append(messages[0])
        
    # 2. Iterate through recent history (e.g., last 4 turns)
    recent_history = messages[-4:] 
    
    for msg in recent_history:
        # 3. Strip old tool outputs to conserve CPU/RAM during inference
        if msg.role == MessageRole.TOOL:
             # Preserve the tool usage metadata, but drop the heavy payload
             msg.content = "[Archived Tool Output]" 
             
        pruned_messages.append(msg)
        
    return pruned_messages

# --- Execution Flow ---
def execute_agent(user_prompt: str, session_memory: Memory):
    # Condense the history before execution
    optimized_messages = prune_memory_for_execution(session_memory)
    
    # The correct way to initialize a temporary modern memory state
    temp_memory = Memory.from_defaults(
        chat_history=optimized_messages
    )
    
    # Run the FunctionAgent 
    response = agent.run(user_prompt, memory=temp_memory)
    
    # Append the NEW prompt and response to the TRUE session memory
    session_memory.put(ChatMessage(role=MessageRole.USER, content=user_prompt))
    session_memory.put(ChatMessage(role=MessageRole.ASSISTANT, content=response.response))
    
    return response

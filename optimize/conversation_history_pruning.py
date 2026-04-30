from llama_index.core.memory import SimpleChatStore
from llama_index.core.memory import SimpleChatMemory # Assuming a modern BaseMemory implementation
from llama_index.core.llms import ChatMessage, MessageRole

def prune_memory_for_execution(raw_memory_state) -> list[ChatMessage]:
    messages = raw_memory_state.get()
    
    if len(messages) <= 5: # Arbitrary short-circuit
        return messages
        
    pruned_messages = []
    
    # 1. Always keep the system prompt
    if messages[0].role == MessageRole.SYSTEM:
        pruned_messages.append(messages[0])
        
    # 2. Iterate through recent history (e.g., last 4 turns)
    # We slice from the end to get the most recent messages
    recent_history = messages[-4:] 
    
    for msg in recent_history:
        # 3. Optional: Strip old tool outputs if they are huge
        # (Only keeping the assistant's final textual response to the user)
        if msg.role == MessageRole.TOOL:
             # Replace massive old tool data with a placeholder to save tokens
             # so the agent knows a tool was used, but doesn't read the old data
             msg.content = "[Archived Tool Output]" 
             
        pruned_messages.append(msg)
        
    return pruned_messages

# --- Execution Flow ---
def execute_agent(user_prompt: str, session_memory):
    # Condense the history before execution
    optimized_messages = prune_memory_for_execution(session_memory)
    
    # Create a temporary memory wrapper for this specific run
    # so the agent only "sees" the pruned context
    temp_memory = SimpleChatMemory.from_chat_store(
        SimpleChatStore(store={"temp": optimized_messages}), 
        chat_store_key="temp"
    )
    
    # Run the agent (Stateless executor pattern)
    response = agent.run(user_prompt, memory=temp_memory)
    
    # Append the NEW prompt and response to the TRUE session memory
    session_memory.put(ChatMessage(role=MessageRole.USER, content=user_prompt))
    session_memory.put(ChatMessage(role=MessageRole.ASSISTANT, content=response.response))
    
    return response

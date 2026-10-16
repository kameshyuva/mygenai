import re
from llama_index.core.llms import ChatMessage, MessageRole

# 1. Put the user's prompt into memory
memory.put(ChatMessage(role=MessageRole.USER, content=query))

# 2. Execute your agent
# Depending on your exact implementation, result is likely an AgentOutput or similar object
result = agent.run(query, memory)

# 3. Extract the final text from the output
# If result is a custom object, adjust this to result.response or result.content
final_response_text = str(result) 

# 4. Strip the thinking block (Regex matching <think>...</think> or <thought>...</thought>)
thinking_pattern = re.compile(r'<(?:think|thought)>.*?</(?:think|thought)>', re.DOTALL | re.IGNORECASE)
cleaned_text = thinking_pattern.sub('', final_response_text).strip()

if not cleaned_text and final_response_text:
    cleaned_text = "[Internal reasoning omitted to save context window]"

# 5. Put the cleaned agent response into memory
memory.put(ChatMessage(role=MessageRole.ASSISTANT, content=cleaned_text))

###################################

from llama_index.core.llms import ChatMessage, MessageRole

# 1. Run the agent (the internal scratchpad handles the <think> blocks temporarily)
handler = agent.run(query, memory)

# 2. Extract the clean text from the AgentOutput
# (Depending on your exact LlamaIndex version, this is usually .response or str(handler))
final_clean_text = str(handler) 

# 3. Manually append the turn to your long-term memory for the next query
memory.put(ChatMessage(role=MessageRole.USER, content=query))
memory.put(ChatMessage(role=MessageRole.ASSISTANT, content=final_clean_text))

####################################

import re
from llama_index.core.llms import MessageRole

# 1. Run your agent
handler = agent.run(query, memory)

# 2. Retrieve the current history containing the thinking blocks
history = memory.get_all()

# 3. Clean the assistant messages in place
thinking_pattern = re.compile(r'<(?:think|thought)>.*?</(?:think|thought)>', re.DOTALL | re.IGNORECASE)

for msg in history:
    if msg.role == MessageRole.ASSISTANT and isinstance(msg.content, str):
        cleaned_content = thinking_pattern.sub('', msg.content).strip()
        
        # Fallback if the model only output a thought
        if not cleaned_content and msg.content:
            cleaned_content = "[Internal reasoning omitted to save context]"
            
        msg.content = cleaned_content

# 4. Overwrite the memory with the cleaned history
memory.set(history)

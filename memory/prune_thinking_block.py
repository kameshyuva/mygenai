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

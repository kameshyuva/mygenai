import re

def caveman_reduce(text: str) -> str:
    # Aggressively strip unnecessary filler words
    stop_words = ["please", "can you", "show me", "i would like to know", "the", "a", "an"]
    pattern = re.compile(r'\b(' + r'|'.join(stop_words) + r')\b\s*', re.IGNORECASE)
    reduced = pattern.sub('', text)
    # Remove extra whitespace
    return re.sub(r'\s+', ' ', reduced).strip()

# Usage before execution
optimized_prompt = caveman_reduce(user_prompt)
response = agent.run(optimized_prompt, memory=user_memory)

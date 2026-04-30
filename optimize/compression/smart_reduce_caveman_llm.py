from llama_index.llms.ollama import Ollama

# Initialize your lightweight model specifically for compression
compressor_llm = Ollama(model="qwen:0.5b", request_timeout=30.0)

def llm_block_compressor(large_text: str) -> str:
    """Uses a fast, quantized local model to strip narrative fluff from large blocks."""
    
    compression_prompt = f"""
    You are a strict data extraction tool. The user has provided a long block of text.
    Extract ONLY the actionable commands, core questions, and technical identifiers (like IDs, errors, or IPs).
    Output as a terse, comma-separated list or short bullet points. 
    DO NOT include pleasantries, explanations, or full sentences.
    
    User Text:
    {large_text}
    
    Extracted Core Intent:
    """
    
    # Run the fast inference
    compressed_result = compressor_llm.complete(compression_prompt).text
    return compressed_result.strip()

def smart_prompt_reduce(user_text: str, char_threshold: int = 400) -> str:
    """Routes the prompt to the appropriate reduction engine based on length."""
    
    # 400 characters is roughly 75-100 tokens. 
    if len(user_text) < char_threshold:
        # Fast, zero-compute regex for standard commands
        return enhanced_caveman_reduce(user_text)
    else:
        # LLM compression for large copy-pasted blocks
        print("[System] Large text detected. Routing to 0.5B compressor...")
        return llm_block_compressor(user_text)

# --- Execution Flow ---
# Original user input could be a quick command OR a 4-paragraph email copy-paste
optimized_prompt = smart_prompt_reduce(raw_user_input)
response = agent.run(optimized_prompt, memory=user_memory)

from llama_index.llms.ollama import Ollama

def get_default_llm() -> Ollama:
    """
    Initializes the local quantized model. 
    Timeout is extended to accommodate local CPU inference and complex tool calling.
    """
    return Ollama(
        model="qwen:4b", 
        request_timeout=300.0,
        temperature=0.1
    )

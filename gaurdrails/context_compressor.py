#pip install tiktoken

import tiktoken
from llama_index.core.llms import ChatMessage, MessageRole
from llama_index.llms.ollama import Ollama

class ContextCompressor:
    def __init__(self, summary_model_name: str = "qwen3.5:0.5b", max_tokens: int = 1500):
        # Dedicated ultra-lightweight model for fast summarization
        self.summarizer = Ollama(model=summary_model_name, request_timeout=45.0)
        self.max_tokens = max_tokens
        # tiktoken executes in microseconds on standard CPUs
        self.tokenizer = tiktoken.get_encoding("cl100k_base") 

    def _count_tokens(self, messages: list[ChatMessage]) -> int:
        """Rapidly calculates token count without waking up an LLM."""
        combined_text = " ".join([m.content for m in messages if m.content])
        return len(self.tokenizer.encode(combined_text))

    def compress_memory_if_needed(self, memory_module) -> None:
        """
        Evaluates current memory length. If it exceeds max_tokens, 
        summarizes older context while keeping recent messages intact.
        """
        current_messages = memory_module.get()
        
        if self._count_tokens(current_messages) < self.max_tokens:
            return # Memory is within safe limits, do nothing
            
        # 1. Identify which messages to summarize vs. keep raw
        # Keep the system prompt (index 0) and the two most recent user/assistant interactions
        system_messages = [m for m in current_messages if m.role == MessageRole.SYSTEM]
        recent_interactions = current_messages[-2:] 
        
        # Everything in between gets compressed
        history_to_compress = [
            m for m in current_messages[:-2] 
            if m.role not in [MessageRole.SYSTEM, MessageRole.TOOL]
        ]
        
        if not history_to_compress:
            return

        # 2. Format the old history for the 0.5B model
        history_text = "\n".join(
            [f"{m.role.value.upper()}: {m.content}" for m in history_to_compress]
        )
        
        prompt = (
            "Summarize the following conversation history focusing on key facts, "
            "established context, and alert assessments. Be extremely concise.\n\n"
            f"{history_text}"
        )

        # 3. Generate summary using the 0.5B model
        summary_response = self.summarizer.complete(prompt).text.strip()

        # 4. Create the new compressed message
        compressed_message = ChatMessage(
            role=MessageRole.ASSISTANT,
            content=f"[System Note: Previous conversation summarized for performance] {summary_response}"
        )

        # 5. Rebuild and overwrite the memory state
        new_memory_state = system_messages + [compressed_message] + recent_interactions
        memory_module.set(new_memory_state)

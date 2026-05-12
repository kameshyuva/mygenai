import asyncio
import threading
from typing import List
from pydantic import Field
from llama_index.core.memory import BaseMemory, ChatMemoryBuffer
from llama_index.core.memory.blocks.base import BaseMemoryBlock
from llama_index.core.llms import ChatMessage, MessageRole

class AsyncRedisAgentMemory(BaseMemory):
    """
    A custom memory manager that entirely bypasses LlamaIndex's buggy SQLite implementation.
    Uses ChatMemoryBuffer + Redis for instant Short-Term Memory, and offloads 
    Long-Term blocks (Facts/Vectors) to a background thread.
    """
    stm_buffer: ChatMemoryBuffer = Field(description="The short-term memory Redis buffer")
    memory_blocks: List[BaseMemoryBlock] = Field(default_factory=list, description="Heavy LTM blocks")

    @classmethod
    def class_name(cls) -> str:
        return "AsyncRedisAgentMemory"

    def get(self, **kwargs) -> List[ChatMessage]:
        """Synchronous Read Phase: Injects Facts/Vectors, then active Chat History."""
        block_msgs = []
        for block in self.memory_blocks:
            block_msgs.extend(block.get(**kwargs))
            
        # Get fast chat history from Redis, truncated perfectly by the buffer
        stm_msgs = self.stm_buffer.get(**kwargs)
        
        return block_msgs + stm_msgs

    def put(self, message: ChatMessage) -> None:
        """Synchronous Write Phase."""
        # 1. Instantly append to Redis chat queue
        self.stm_buffer.put(message)

        # 2. Trigger background extraction ONLY after the AI replies.
        # This gives the background LLM both the User's prompt and AI's answer for context.
        if message.role == MessageRole.ASSISTANT:
            try:
                loop = asyncio.get_running_loop()
                loop.run_in_executor(None, self._background_update)
            except RuntimeError:
                threading.Thread(target=self._background_update).start()

    def _background_update(self) -> None:
        """Executes Fact and Vector updates in the background thread."""
        try:
            # Grab the last 2 messages (User + AI) to provide context for extraction
            context_messages = self.stm_buffer.get_all()[-2:]
            
            for block in self.memory_blocks:
                # Blocks expect lists of messages
                block.put(context_messages)
            print("\n[Background Memory] ✅ Fact and Vector Extraction Complete.")
        except Exception as e:
            print(f"\n[Background Memory] ❌ Error updating memory blocks: {e}")

    # --- Standard BaseMemory Interface Requirements ---
    def get_all(self) -> List[ChatMessage]:
        return self.stm_buffer.get_all()

    def set(self, messages: List[ChatMessage]) -> None:
        self.stm_buffer.set(messages)

    def reset(self) -> None:
        self.stm_buffer.reset()

import asyncio
import threading
from typing import List
from pydantic import Field
from llama_index.core.memory import BaseMemory, ChatMemoryBuffer
from llama_index.core.memory.blocks.base import BaseMemoryBlock
from llama_index.core.llms import ChatMessage, MessageRole

class AsyncRedisAgentMemory(BaseMemory):
    """
    Final optimized memory manager. 
    Supports both sync (put/get) and async (aput/aget) workflows.
    """
    stm_buffer: ChatMemoryBuffer = Field(description="The short-term memory Redis buffer")
    memory_blocks: List[BaseMemoryBlock] = Field(default_factory=list, description="Heavy LTM blocks")

    @classmethod
    def class_name(cls) -> str:
        return "AsyncRedisAgentMemory"

    # ==========================================
    # ASYNCHRONOUS METHODS (Recommended for Production)
    # ==========================================
    async def aget(self, **kwargs) -> List[ChatMessage]:
        """Async Read: Fetches history and LTM context from Redis concurrently."""
        # 1. Fetch from all LTM blocks and STM buffer in parallel
        tasks = [block.aget(**kwargs) for block in self.memory_blocks]
        tasks.append(self.stm_buffer.aget(**kwargs))
        
        results = await asyncio.gather(*tasks)
        
        # Flatten the list of lists
        return [msg for sublist in results for msg in sublist]

    async def aput(self, message: ChatMessage) -> None:
        """Async Write: Saves message to STM instantly, offloads LTM to background."""
        # 1. Save to Redis STM immediately so the next turn has context
        await self.stm_buffer.aput(message)

        # 2. If the AI finished talking, trigger background extraction
        if message.role == MessageRole.ASSISTANT:
            # We use create_task to "fire and forget" the heavy LLM work
            asyncio.create_task(self._abackground_update())

    async def _abackground_update(self) -> None:
        """The heavy lifting async task for Fact/Vector extraction."""
        try:
            # Grab the last interaction (User + AI)
            all_msgs = await self.stm_buffer.aget_all()
            context_messages = all_msgs[-2:]
            
            # Run heavy extractions
            await asyncio.gather(*[block.aput(context_messages) for block in self.memory_blocks])
            print("\n[Background Task] ✅ Async Fact/Vector Extraction Complete.")
        except Exception as e:
            print(f"\n[Background Task] ❌ Error: {e}")

    # ==========================================
    # SYNCHRONOUS METHODS (Fallback/Scripts)
    # ==========================================
    def get(self, **kwargs) -> List[ChatMessage]:
        block_msgs = []
        for block in self.memory_blocks:
            block_msgs.extend(block.get(**kwargs))
        stm_msgs = self.stm_buffer.get(**kwargs)
        return block_msgs + stm_msgs

    def put(self, message: ChatMessage) -> None:
        self.stm_buffer.put(message)
        if message.role == MessageRole.ASSISTANT:
            try:
                loop = asyncio.get_running_loop()
                loop.run_in_executor(None, self._background_update)
            except RuntimeError:
                threading.Thread(target=self._background_update).start()

    def _background_update(self) -> None:
        try:
            context_messages = self.stm_buffer.get_all()[-2:]
            for block in self.memory_blocks:
                block.put(context_messages)
            print("\n[Background Thread] ✅ Sync Fact/Vector Extraction Complete.")
        except Exception as e:
            print(f"\n[Background Thread] ❌ Error: {e}")

    def get_all(self) -> List[ChatMessage]:
        return self.stm_buffer.get_all()

    def set(self, messages: List[ChatMessage]) -> None:
        self.stm_buffer.set(messages)

    def reset(self) -> None:
        self.stm_buffer.reset()

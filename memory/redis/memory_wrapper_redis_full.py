import asyncio
import threading
import json
from pydantic import Field
from typing import Any, List

from llama_index.core.memory import Memory
from llama_index.core.memory.blocks import FactExtractionMemoryBlock
from llama_index.core.llms import ChatMessage

# Importing the redis client from our local storage file
from storage import get_raw_redis_client

class AsyncBackgroundMemory(Memory):
    """
    Modern Memory wrapper that offloads heavy LTM updates (Facts/Vectors) 
    to background threads/tasks while persisting facts to Redis.
    """
    name: str = Field(default="AsyncBackgroundMemory", description="The custom background memory manager")

    @classmethod
    def class_name(cls) -> str:
        return "AsyncBackgroundMemory"

    # ==========================================
    # SYNCHRONOUS OVERRIDES (For agent.run / agent.chat)
    # ==========================================
    def put(self, message: ChatMessage) -> None:
        """
        Saves to Short-Term Memory immediately, then offloads 
        heavy block updates to a background thread.
        """
        # We manually call the internal chat store put to ensure STM is updated instantly
        self.chat_store.add_message(self.chat_store_key, message)

        # Offload the LTM update (Facts/Vectors) to a background thread
        try:
            loop = asyncio.get_running_loop()
            # Use the loop's executor to run the sync background update
            loop.run_in_executor(None, self._background_update)
        except RuntimeError:
            # Fallback if no event loop is running (standard script)
            threading.Thread(target=self._background_update).start()

    def _background_update(self) -> None:
        """The heavy lifting thread: Extraction and Redis Persistence."""
        try:
            # Trigger the standard LlamaIndex block update logic
            # This calls FactExtraction (LLM) and VectorMemory (Embedding)
            super()._update_memory_blocks()

            # Manually persist Facts to Redis since the block is RAM-only
            self._persist_facts_to_redis()
            
            print(f"[Background Thread] ✅ Memory blocks updated and facts persisted.")
        except Exception as e:
            print(f"[Background Thread] ❌ Error in background update: {e}")

    # ==========================================
    # ASYNCHRONOUS OVERRIDES (For agent.arun / agent.achat)
    # ==========================================
    async def aput(self, message: ChatMessage) -> None:
        """
        Async version: Saves to STM and fires an async background task.
        """
        await self.chat_store.amessage_put(self.chat_store_key, message)
        
        # Fire and forget the async background update
        asyncio.create_task(self._async_background_update())

    async def _async_background_update(self) -> None:
        """The heavy lifting async task."""
        try:
            await super()._aupdate_memory_blocks()
            self._persist_facts_to_redis()
            print(f"[Background Task] ✅ Async update and persistence complete.")
        except Exception as e:
            print(f"[Background Task] ❌ Error in async background update: {e}")

    # ==========================================
    # HELPER: REDIS PERSISTENCE
    # ==========================================
    def _persist_facts_to_redis(self) -> None:
        """
        Loops through blocks to find the FactExtractionMemoryBlock 
        and saves its facts list to Redis.
        """
        for block in self.memory_blocks:
            if isinstance(block, FactExtractionMemoryBlock):
                try:
                    r = get_raw_redis_client()
                    # We use the chat_store_key as the unique identifier for the facts
                    redis_key = f"facts_{self.chat_store_key}"
                    r.set(redis_key, json.dumps(block.facts))
                except Exception as e:
                    print(f"[Memory Wrapper] Failed to save facts to Redis: {e}")

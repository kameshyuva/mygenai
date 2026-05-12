import asyncio
import threading
from pydantic import Field
from llama_index.core.memory import Memory

class AsyncioBackgroundMemory(Memory):
    """
    A custom memory wrapper that uses asyncio's event loop to offload 
    memory writes to the background. Supports both sync and async agent execution.
    """
    name: str = Field(default="AsyncioBackgroundMemory", description="The custom background memory manager")
    
    @classmethod
    def class_name(cls) -> str:
        return "AsyncioBackgroundMemory"

    # ==========================================
    # SYNCHRONOUS OVERRIDES (For agent.chat)
    # ==========================================
    def put(self, *args, **kwargs):
        """
        Overrides the synchronous put method.
        """
        try:
            loop = asyncio.get_running_loop()
            loop.run_in_executor(None, self._background_update, *args, **kwargs)
        except RuntimeError:
            threading.Thread(
                target=self._background_update, 
                args=args, 
                kwargs=kwargs
            ).start()

    def _background_update(self, *args, **kwargs):
        """
        Executes the synchronous memory block updates in a thread pool.
        """
        try:
            super().put(*args, **kwargs)
            print("[Asyncio Executor] Heavy memory update completed.")
        except Exception as e:
            print(f"[Asyncio Executor] Error updating memory blocks: {e}")

    # ==========================================
    # ASYNCHRONOUS OVERRIDES (For agent.achat)
    # ==========================================
    async def aput(self, *args, **kwargs):
        """
        Overrides the asynchronous aput method.
        """
        # Fire and forget: Schedules the coroutine to run in the background 
        # without awaiting it, instantly freeing up the main event loop.
        asyncio.create_task(self._async_background_update(*args, **kwargs))

    async def _async_background_update(self, *args, **kwargs):
        """
        Executes the asynchronous memory block updates as a background task.
        """
        try:
            await super().aput(*args, **kwargs)
            print("[Asyncio Task] Heavy async memory update completed.")
        except Exception as e:
            print(f"[Asyncio Task] Error updating memory blocks: {e}")

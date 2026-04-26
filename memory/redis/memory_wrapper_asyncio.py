import asyncio
import threading
from llama_index.core.memory import Memory

class AsyncioBackgroundMemory(Memory):
    """
    A custom memory wrapper that uses asyncio's event loop to offload 
    memory writes to a background executor thread.
    """
    def put(self, *args, **kwargs):
        """
        Overrides the synchronous put method.
        """
        try:
            # Attempt to get the current running asyncio event loop 
            # (e.g., if running inside FastAPI or an async context)
            loop = asyncio.get_running_loop()
            
            # Offload the synchronous update to the loop's default ThreadPoolExecutor.
            # Passing 'None' as the first argument uses the default executor.
            loop.run_in_executor(None, self._background_update, *args, **kwargs)
            
        except RuntimeError:
            # Fallback: If this is called in a purely synchronous script 
            # where no asyncio event loop is running, spawn a basic OS thread.
            threading.Thread(
                target=self._background_update, 
                args=args, 
                kwargs=kwargs
            ).start()

    def _background_update(self, *args, **kwargs):
        """
        Executes the actual memory block updates in the background.
        """
        try:
            super().put(*args, **kwargs)
            print("[Asyncio Executor] Heavy memory update completed.")
        except Exception as e:
            print(f"[Asyncio Executor] Error updating memory blocks: {e}")

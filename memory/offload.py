import concurrent.futures
from llama_index.core.memory import Memory
from llama_index.core.memory.blocks import FactExtractionMemoryBlock, VectorMemoryBlock

class ThreadedBackgroundMemory(Memory):
    def __init__(self, max_workers: int = 1, **kwargs):
        super().__init__(**kwargs)
        # Initialize a thread pool. 
        # Keep max_workers low to prevent CPU contention.
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)

    def put(self, *args, **kwargs):
        """
        Overrides the synchronous put method.
        Instead of blocking, it submits the update to a thread pool.
        """
        self._executor.submit(self._background_update, *args, **kwargs)

    def _background_update(self, *args, **kwargs):
        """
        Executes the actual heavy memory block updates in the background.
        """
        try:
            # Calls the original Memory.put() logic, which loops 
            # through your memory blocks and triggers the LLM/Embedding calls.
            super().put(*args, **kwargs)
            print("Background memory update completed successfully.")
        except Exception as e:
            # Handle logging so thread exceptions aren't silently swallowed
            print(f"Error updating memory blocks in background: {e}")

#pip install llama-index-core llama-index-llms-ollama llama-index-vector-stores-redis llama-index-storage-kvstore-redis redis


import concurrent.futures
from llama_index.core.memory import Memory

class ThreadedBackgroundMemory(Memory):
    """
    A custom memory wrapper that executes memory writes (put) in a background thread
    to prevent heavy extraction tasks from blocking the main application flow.
    """
    def __init__(self, max_workers: int = 1, **kwargs):
        super().__init__(**kwargs)
        # Using a single worker to prevent CPU contention on CPU-only machines
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)

    def put(self, *args, **kwargs):
        """
        Overrides the synchronous put method to submit the update to the thread pool.
        """
        self._executor.submit(self._background_update, *args, **kwargs)

    def _background_update(self, *args, **kwargs):
        """
        Executes the actual memory block updates in the background.
        """
        try:
            super().put(*args, **kwargs)
            print("[Background Thread] Heavy memory update completed.")
        except Exception as e:
            print(f"[Background Thread] Error updating memory blocks: {e}")

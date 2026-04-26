import concurrent.futures
from typing import Any

class BackgroundBlock:
    """
    A wrapper that offloads .put() calls to a thread pool.
    Retrieval (.get()) remains synchronous.
    """
    def __init__(self, block: Any, executor: concurrent.futures.ThreadPoolExecutor):
        self._block = block
        self._executor = executor

    def put(self, message: Any) -> None:
        # Fire-and-forget: The agent continues while the thread works
        self._executor.submit(self._block.put, message)

    def get(self, **kwargs) -> Any:
        # Must be sync so the agent can see existing memory context
        return self._block.get(**kwargs)

    def __getattr__(self, name):
        # Forward any other attributes (reset, delete, etc.) to the real block
        return getattr(self._block, name)

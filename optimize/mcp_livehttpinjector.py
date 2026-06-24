import httpx

class LiveHttpInjector:
    def __init__(self, request_headers: dict):
        # Extract only what you need (primitive strings are perfectly pickle-safe)
        self.auth_token = request_headers.get("Authorization")
        
        # Create the live async client that BasicMCPClient will use
        self.http_client = httpx.AsyncClient(
            headers={"Authorization": self.auth_token}
        )

    def __getstate__(self):
        # 🛡️ THE SHIELD: Tell the 0.14.x telemetry engine to ignore the live HTTP client
        state = self.__dict__.copy()
        if 'http_client' in state:
            del state['http_client']
        return state

    def __setstate__(self, state):
        # Restore the safe state
        self.__dict__.update(state)
        # Re-initialize the live client if LlamaIndex tries to recreate the object
        self.http_client = httpx.AsyncClient(
            headers={"Authorization": getattr(self, 'auth_token', '')}
        )

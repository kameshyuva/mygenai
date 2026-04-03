from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
from contextvars import ContextVar
from mcp.server import Server

# 1. Define the ContextVar
current_headers = ContextVar("current_headers", default={})

app = FastAPI()
mcp = Server("my-mcp-server")

# 2. Create a Middleware to handle headers for ALL concurrent users
class HeaderContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # This runs uniquely for EVERY incoming user request.
        # It sets the headers only for the current asyncio task.
        token = current_headers.set(dict(request.headers))
        
        try:
            # Pass the request down to the /mcp endpoint
            response = await call_next(request)
            return response
        finally:
            # Clean up the context after the request finishes to prevent memory leaks
            current_headers.reset(token)

# Register the middleware
app.add_middleware(HeaderContextMiddleware)


# 3. Your MCP Tool safely accesses the task-isolated headers
@mcp.tool()
async def target_mcp_tool(query: str) -> str:
    # Even if 1,000 users are hitting this tool at the exact same time,
    # ContextVar guarantees this will ONLY return the headers for the current user.
    headers = current_headers.get()
    
    auth_token = headers.get("authorization")
    if not auth_token:
        return "Error: Unauthorized."
        
    return f"Processed query '{query}' securely."

# 4. Your Streamable Endpoint
@app.api_route("/mcp", methods=["GET", "POST"])
async def handle_mcp_stream(request: Request):
    # You no longer need to manually set headers here! 
    # The middleware already did it for this specific user's task.
    
    body = await request.body()
    
    async def generate_mcp_response():
        # Stream processing logic goes here...
        yield b'{"jsonrpc": "2.0", "id": 1, "result": {"content": "..."}}'

    return StreamingResponse(generate_mcp_response(), media_type="application/json")

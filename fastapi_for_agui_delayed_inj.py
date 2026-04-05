# main.py
import uvicorn
from fastapi import FastAPI, Request
from contextlib import asynccontextmanager

# Import your existing async builder class
# from your_custom_module import YourAsyncAgentBuilder

from agui_bridge import (
    AGUIBridgeRouter, 
    username_var, 
    realm_var, 
    app_token_var
)

# 1. Instantiate the bridge immediately so its router can be mounted
agui_bridge = AGUIBridgeRouter(router_model="llama3")

# 2. Define the Lifespan event to handle async initialization
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting server: Building core async agent...")
    
    # Await your separate class to build the agent
    # builder = YourAsyncAgentBuilder()
    # my_async_agent = await builder.get_agent()
    
    # Inject the built agent into the bridge
    # agui_bridge.set_core_agent(my_async_agent)
    print("Agent built and injected successfully.")
    
    yield # The FastAPI server processes requests during this yield
    
    # Optional cleanup logic can go here during shutdown
    print("Shutting down server.")

# 3. Attach the lifespan to your FastAPI app
app = FastAPI(title="Unified Agent API", lifespan=lifespan)

# --- MIDDLEWARE ---
@app.middleware("http")
async def capture_headers_middleware(request: Request, call_next):
    username_var.set(request.headers.get("username"))
    realm_var.set(request.headers.get("realm"))
    app_token_var.set(request.headers.get("app-token"))
    return await call_next(request)

# --- ROUTER MOUNTING ---
app.include_router(agui_bridge.router, prefix="/api/copilotkit")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)

#pip install slowapi

import asyncio
from fastapi import FastAPI, HTTPException, Request, Depends
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from llama_index.core.agent import FunctionAgent
from llama_index.core.memory import Memory
from llama_index.llms.ollama import Ollama

app = FastAPI()

# ---------------------------------------------------------
# 1. Resource Guardrails Setup
# ---------------------------------------------------------
# Rate Limiter: Track users by IP address
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Concurrency Limiter: Lock inference to a maximum of 1 or 2 concurrent tasks.
# On an 8-core machine, forcing Ollama to process one 9B request at a time 
# is usually faster than processing two simultaneously due to context switching.
MAX_CONCURRENT_LLM_REQUESTS = 1
inference_semaphore = asyncio.Semaphore(MAX_CONCURRENT_LLM_REQUESTS)

# ---------------------------------------------------------
# 2. LLM Configuration (Timeouts & Token Limits)
# ---------------------------------------------------------
llm_main = Ollama(
    model="qwen3.5:9b", 
    request_timeout=90.0, # Hard timeout: Kill request if model hangs for 90s
    additional_kwargs={
        "num_predict": 250, # Max tokens to generate per response (prevents infinite loops)
        "num_thread": 6     # Leave 2 cores free for the OS, FastAPI, and MCP servers
    }
)

# Assume your tools and agent are initialized here as before
# agent = FunctionAgent.from_tools(..., llm=llm_main, memory=Memory())

# ---------------------------------------------------------
# 3. Protected Endpoint
# ---------------------------------------------------------
class ChatRequest(BaseModel):
    query: str

@app.post("/api/v1/agent/chat")
@limiter.limit("5/minute") # Strict API rate limit: 5 requests per minute per IP
async def secure_chat(request: Request, body: ChatRequest):
    """
    Endpoint protected by:
    1. IP-based rate limiting (5 req/min)
    2. Semaphore-based concurrency limiting (Max 1 active LLM call)
    """
    
    # Check if the server is currently bogged down before acquiring the lock
    if inference_semaphore.locked():
        # Optional: Return a 503 instead of making the user wait in a long queue
        raise HTTPException(
            status_code=503, 
            detail="Server is currently processing at maximum capacity. Please try again in a few seconds."
        )

    # Acquire the lock to execute inference
    async with inference_semaphore:
        try:
            # Run the agent in a threadpool so it doesn't block FastAPI's async event loop
            # This ensures other endpoints (like health checks) stay responsive
            agent_response = await asyncio.to_thread(agent.chat, body.query)
            
            return {"response": agent_response.response}
            
        except TimeoutError:
            raise HTTPException(status_code=504, detail="Inference timed out.")
        except Exception as e:
            raise HTTPException(status_code=500, detail="Internal server error during inference.")

import asyncio
from fastapi import FastAPI, HTTPException, Request, Depends
from pydantic import BaseModel
# Assume agent, Memory, and Ollama are initialized here as before
from guardrails import AgentGuardrails, SecurityViolationError

app = FastAPI()

# 1. Initialize the unified guardrail class (contains deterministic + 0.5B semantic checks)
guardrails = AgentGuardrails(semantic_model_name="qwen3.5:0.5b", timeout=15.0)

# 2. Lock the CPU to process one full pipeline (Generation + Evaluation) at a time
cpu_lock = asyncio.Semaphore(1)

class ChatRequest(BaseModel):
    query: str

@app.post("/api/v1/agent/chat")
async def secure_chat_realtime(request: ChatRequest):
    body = await request.json()
    raw_query = body.get("query", "")
    
    # ---------------------------------------------------------
    # STEP 1: Real-Time Input Sanitization (Deterministic)
    # ---------------------------------------------------------
    try:
        # Executes in milliseconds (Regex, Presidio PII, Profanity)
        safe_query = guardrails.sanitize_input(raw_query)
    except SecurityViolationError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # ---------------------------------------------------------
    # STEP 2: CPU-Locked Sequential Execution
    # ---------------------------------------------------------
    if cpu_lock.locked():
        raise HTTPException(status_code=503, detail="Server busy. Try again shortly.")

    async with cpu_lock:
        try:
            # A. Generate Response (9B Model)
            # Offloaded to a thread so FastAPI's async event loop isn't blocked
            agent_response = await asyncio.to_thread(agent.chat, safe_query)
            final_text = agent_response.response
            
            # B. Real-Time Output Evaluation (0.5B Model + Deterministic)
            # The 8 cores shift entirely to the 0.5B model for a rapid YES/NO check
            is_safe = await asyncio.to_thread(guardrails.validate_output, final_text)
            
            if not is_safe:
                # Blocks the response from ever leaving the server
                raise HTTPException(status_code=403, detail="Response blocked by security policies.")
                
            # C. Return the verified response
            return {"response": final_text}
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Inference pipeline error: {str(e)}")

from fastapi import FastAPI, HTTPException, Request, Depends
from pydantic import BaseModel, Field
from llama_index.core.agent import FunctionAgent
from llama_index.core.memory import Memory
from llama_index.llms.ollama import Ollama
from llama_index.core.tools import FunctionTool

# Import the new decoupled class and exception
from guardrails import AgentGuardrails, SecurityViolationError

app = FastAPI()

# ---------------------------------------------------------
# 1. Global Instances
# ---------------------------------------------------------
# Instantiate the guardrail manager (loads dictionaries and models once)
guardrails = AgentGuardrails(semantic_model_name="qwen3.5:0.5b")

# Main reasoning model
llm_main = Ollama(model="qwen3.5:9b", request_timeout=120.0)

# ---------------------------------------------------------
# 2. Tools & Agent Initialization
# ---------------------------------------------------------
class AlertAssessmentSchema(BaseModel):
    alert_id: str = Field(..., description="The exact ID of the alert.")
    assessment_level: int = Field(..., ge=1, le=5, description="Priority rank from 1 to 5.")

def assess_alert(alert_id: str, assessment_level: int) -> str:
    return f"Alert {alert_id} assessed at level {assessment_level}."

alert_tool = FunctionTool.from_defaults(fn=assess_alert, fn_schema=AlertAssessmentSchema)

agent = FunctionAgent.from_tools(
    tools=[alert_tool],
    llm=llm_main,
    system_prompt="You are a secure system agent designed for business alert assessment. ONLY use the provided tools.",
    memory=Memory(),
    verbose=True
)

# ---------------------------------------------------------
# 3. FastAPI Dependencies & Routes
# ---------------------------------------------------------
async def get_safe_query(request: Request):
    """FastAPI dependency to extract and sanitize user input."""
    body = await request.json()
    raw_query = body.get("query", "")
    
    try:
        # Use the class to sanitize and redact PII
        safe_query = guardrails.sanitize_input(raw_query)
        return safe_query
    except SecurityViolationError as e:
        # Map the internal guardrail error to a 400 HTTP response
        raise HTTPException(status_code=400, detail=str(e))

class ChatRequest(BaseModel):
    query: str

@app.post("/api/v1/agent/chat")
async def secure_chat(request: ChatRequest, safe_query: str = Depends(get_safe_query)):
    try:
        # 1. Execute agent with sanitized input
        agent_response = agent.chat(safe_query)
        final_text = agent_response.response
        
        # 2. Use the class to validate output safety
        if not guardrails.validate_output(final_text):
             raise HTTPException(status_code=403, detail="Response blocked by output guardrails.")
             
        return {"response": final_text}

    except ValueError as e:
        # Catches Pydantic schema errors if the 9B model fails to fix tool arguments
        raise HTTPException(status_code=422, detail=f"Structural validation failed: {str(e)}")

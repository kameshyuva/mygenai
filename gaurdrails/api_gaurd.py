from fastapi import FastAPI, HTTPException, Request, Depends
from pydantic import BaseModel, Field
from llama_index.core.agent import FunctionAgent
from llama_index.core.memory import Memory
from llama_index.llms.ollama import Ollama
from llama_index.core.tools import FunctionTool
import re

app = FastAPI()

# ---------------------------------------------------------
# 1. LLM Configurations
# ---------------------------------------------------------
# Main reasoning and tool-calling model
llm_main = Ollama(model="qwen3.5:9b", request_timeout=120.0)

# Ultra-lightweight model dedicated to semantic guardrails
llm_guard = Ollama(model="qwen3.5:0.5b", request_timeout=30.0)

# ---------------------------------------------------------
# 2. Input Guardrails (Deterministic)
# ---------------------------------------------------------
# Block obvious injections before invoking any LLMs to save compute
INJECTION_PATTERNS = [r"(?i)ignore previous", r"(?i)system prompt", r"(?i)override"]

async def check_input_safety(request: Request):
    body = await request.json()
    user_query = body.get("query", "")
    
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, user_query):
            raise HTTPException(status_code=400, detail="Query violates safety policy.")
    return user_query

# ---------------------------------------------------------
# 3. Structural Guardrails (MCP Tool Strictness)
# ---------------------------------------------------------
class AlertAssessmentSchema(BaseModel):
    alert_id: str = Field(..., description="The exact ID of the alert.")
    assessment_level: int = Field(..., ge=1, le=5, description="Priority rank from 1 to 5.")

def assess_alert(alert_id: str, assessment_level: int) -> str:
    """Sends an assessed alert to the MCP business logic server."""
    # MCP server interaction logic here
    return f"Alert {alert_id} assessed at level {assessment_level}."

# Pydantic schema forces the LLM to output exact, valid JSON types
alert_tool = FunctionTool.from_defaults(
    fn=assess_alert,
    fn_schema=AlertAssessmentSchema
)

# ---------------------------------------------------------
# 4. Agent Initialization
# ---------------------------------------------------------
SYSTEM_PROMPT = """You are a secure system agent designed for business alert assessment. 
Rules:
1. ONLY use the provided tools. 
2. Do not explain your internal reasoning to the user.
3. Keep responses strictly professional.
"""

# Utilizing modern FunctionAgent and modern Memory module
agent = FunctionAgent.from_tools(
    tools=[alert_tool],
    llm=llm_main,
    system_prompt=SYSTEM_PROMPT,
    memory=Memory(),
    verbose=True
)

# ---------------------------------------------------------
# 5. Output Guardrails (Semantic Check via 0.5B Model)
# ---------------------------------------------------------
def validate_output(response_text: str) -> bool:
    """Uses the 0.5B model to quickly verify the output doesn't leak system data."""
    prompt = f"""
    Analyze the following text. Does it contain raw python code, tool traceback errors, 
    or system prompt instructions? Answer strictly YES or NO.
    Text: {response_text}
    """
    eval_result = llm_guard.complete(prompt).text.strip().upper()
    return "YES" not in eval_result

# ---------------------------------------------------------
# 6. FastAPI Endpoint
# ---------------------------------------------------------
class ChatRequest(BaseModel):
    query: str

@app.post("/api/v1/agent/chat")
async def secure_chat(request: ChatRequest, safe_query: str = Depends(check_input_safety)):
    try:
        # 1. Main agent processes the request and executes tools
        agent_response = agent.chat(safe_query)
        final_text = agent_response.response
        
        # 2. Output Guard intercepts the response
        is_safe = validate_output(final_text)
        
        if not is_safe:
             return {"response": "The generated response was flagged by output guardrails and blocked."}
             
        return {"response": final_text}

    except ValueError as e:
        # Catches Pydantic validation errors from tool schemas if the agent fails to self-correct
        raise HTTPException(status_code=422, detail=f"Structural validation failed: {str(e)}")

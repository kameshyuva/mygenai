#pip install better_profanity presidio-analyzer presidio-anonymizer
#python -m spacy download en_core_web_lg 


from fastapi import FastAPI, HTTPException, Request, Depends
from pydantic import BaseModel, Field
from llama_index.core.agent import FunctionAgent
from llama_index.core.memory import Memory
from llama_index.llms.ollama import Ollama
from llama_index.core.tools import FunctionTool

from better_profanity import profanity
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
import re

app = FastAPI()

# ---------------------------------------------------------
# 1. Initialize Local Guardrail Engines
# ---------------------------------------------------------
profanity.load_censor_words() # Loads default offline dictionary
analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()

llm_main = Ollama(model="qwen3.5:9b", request_timeout=120.0)
llm_guard = Ollama(model="qwen3.5:0.5b", request_timeout=30.0)

# ---------------------------------------------------------
# 2. Input Guardrails (Profanity + PII + Injection)
# ---------------------------------------------------------
INJECTION_PATTERNS = [r"(?i)ignore previous", r"(?i)system prompt", r"(?i)override"]

async def sanitize_input(request: Request):
    body = await request.json()
    raw_query = body.get("query", "")
    
    # 2a. Fast Profanity Check
    if profanity.contains_profanity(raw_query):
        raise HTTPException(status_code=400, detail="Query contains inappropriate language.")

    # 2b. Fast Injection Check
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, raw_query):
            raise HTTPException(status_code=400, detail="Query violates safety policy.")

    # 2c. PII Redaction (Anonymize before it hits the LLM)
    # Detects emails, phones, credit cards, IP addresses, etc.
    analyzer_results = analyzer.analyze(text=raw_query, language='en')
    anonymized_result = anonymizer.anonymize(text=raw_query, analyzer_results=analyzer_results)
    
    # Returns the sanitized query (e.g., "Assess alert for user <EMAIL_ADDRESS>")
    return anonymized_result.text

# ---------------------------------------------------------
# 3. Structural Guardrails & Agent
# ---------------------------------------------------------
class AlertAssessmentSchema(BaseModel):
    alert_id: str = Field(..., description="The exact ID of the alert.")
    assessment_level: int = Field(..., ge=1, le=5, description="Priority rank from 1 to 5.")

def assess_alert(alert_id: str, assessment_level: int) -> str:
    """Sends an assessed alert to the MCP business logic server."""
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
# 4. Output Guardrails (Profanity + Leakage + Semantic)
# ---------------------------------------------------------
def validate_output(response_text: str) -> bool:
    # 4a. Check if the LLM generated profanity
    if profanity.contains_profanity(response_text):
        return False
        
    # 4b. Check if the LLM leaked internal PII (e.g., a real user's email from the DB)
    pii_results = analyzer.analyze(text=response_text, language='en')
    if len(pii_results) > 0:
        # Flagged if any PII is detected in the outgoing message
        return False

    # 4c. Semantic check using the 0.5B model for system prompt/traceback leaks
    prompt = f"""
    Analyze the following text. Does it contain raw python code, tool traceback errors, 
    or system prompt instructions? Answer strictly YES or NO.
    Text: {response_text}
    """
    eval_result = llm_guard.complete(prompt).text.strip().upper()
    return "YES" not in eval_result

# ---------------------------------------------------------
# 5. FastAPI Endpoint
# ---------------------------------------------------------
class ChatRequest(BaseModel):
    query: str

@app.post("/api/v1/agent/chat")
async def secure_chat(request: ChatRequest, safe_query: str = Depends(sanitize_input)):
    try:
        # Execute the main agent with the PII-scrubbed, safe query
        agent_response = agent.chat(safe_query)
        final_text = agent_response.response
        
        # Run final strict output validation
        if not validate_output(final_text):
             raise HTTPException(status_code=403, detail="The generated response was blocked by output guardrails.")
             
        return {"response": final_text}

    except ValueError as e:
        raise HTTPException(status_code=422, detail=f"Structural validation failed: {str(e)}")

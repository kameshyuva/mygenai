import os
import asyncio
from fastapi import FastAPI
from pydantic import BaseModel
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.llms.ollama import Ollama

from prompt_manager import PromptManager

app = FastAPI()

CHROMA_HOST = os.getenv("CHROMA_HOST", "localhost")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", 8000))

# Initialize Manager
prompt_manager = PromptManager(host=CHROMA_HOST, port=CHROMA_PORT)

# Initialize Model and Agent
llm = Ollama(model="llama3.1", request_timeout=120.0)

agent = FunctionAgent(
    name="EnterpriseAgent",
    description="Data retrieval agent",
    tools=[], 
    llm=llm,
    system_prompt=prompt_manager.get_system_prompt()
)

# --- Standard Query Endpoint ---
class QueryPayload(BaseModel):
    query: str

@app.post("/api/query")
async def execute_query(payload: QueryPayload):
    final_user_message = prompt_manager.build_user_message(payload.query)
    response = await agent.run(user_msg=final_user_message)

    return {
        "status": "success",
        "data": str(response)
    }

# --- NEW: Dynamic Example Injection Endpoint ---
class ExamplePayload(BaseModel):
    query: str
    response: str

@app.post("/api/examples")
async def add_new_example(payload: ExamplePayload):
    """Adds a new query/response pair to the ChromaDB vector store."""
    prompt_manager.add_example(query=payload.query, response=payload.response)
    
    return {
        "status": "success",
        "message": f"Successfully added example for query: '{payload.query}'"
    }

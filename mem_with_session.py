import uuid
from typing import Dict, Optional
from fastapi import FastAPI
from pydantic import BaseModel
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.core.memory import Memory
from llama_index.llms.openai import OpenAI

app = FastAPI()

# 1. Global State & Agent Initialization
llm = OpenAI(model="gpt-4o")
agent = FunctionAgent(name="DynamicBot", tools=[], llm=llm)
session_store: Dict[str, Memory] = {}

# 2. Define the expected API Request Body
class ChatRequest(BaseModel):
    message: str
    # session_id is optional. If the client doesn't send it, it's a new chat.
    session_id: Optional[str] = None 

# 3. Memory Retrieval Logic
def get_or_create_memory(session_id: str) -> Memory:
    if session_id not in session_store:
        session_store[session_id] = Memory.from_defaults(
            session_id=session_id, 
            token_limit=3000
        )
    return session_store[session_id]

# 4. The API Endpoint
@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    # --- DYNAMIC SESSION ID LOGIC ---
    # If the client provided a session_id, use it. Otherwise, generate a new UUID.
    active_session_id = request.session_id or str(uuid.uuid4())
    
    print(f"[{active_session_id}] Received message: {request.message}")
    
    # Retrieve the user's specific memory
    user_memory = get_or_create_memory(active_session_id)
    
    # Run the agent
    response = await agent.run(request.message, memory=user_memory)
    
    # Return both the agent's answer AND the session_id
    # The client must save this session_id and send it back in their next request!
    return {
        "session_id": active_session_id,
        "response": str(response)
    }

# Run this script using: uvicorn filename:app --reload

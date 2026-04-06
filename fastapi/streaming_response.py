from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from llama_index.core.agent.workflow import AgentStream

app = FastAPI(title="LlamaIndex Workflow Memory Streaming API")

class ChatRequest(BaseModel):
    prompt: str
    session_id: str  # To identify which user's memory to load

# ---------------------------------------------------------
# Your Existing Setup
# ---------------------------------------------------------

# 1. You likely have a globally initialized workflow agent
global_agent = ... # Your FunctionAgent initialized with Ollama and MCP tools

def get_memory_for_session(session_id: str):
    """
    Retrieve or initialize the memory object for the given session.
    """
    # Example:
    # return ChatMemoryBuffer.from_defaults(
    #     chat_store=my_redis_store, 
    #     chat_store_key=session_id
    # )
    pass

# ---------------------------------------------------------
# The Endpoint
# ---------------------------------------------------------

@app.post("/stream_chat")
async def stream_chat_endpoint(request: ChatRequest):
    
    async def event_generator():
        try:
            # 1. Fetch the memory for this specific user/session
            session_memory = get_memory_for_session(request.session_id)
            
            # 2. Start the workflow handler without awaiting it.
            # Pass BOTH the prompt and the dynamically loaded memory 
            # exactly as your custom method requires.
            handler = global_agent.run(
                user_msg=request.prompt, 
                memory=session_memory
            )
            
            # 3. Iterate over the internal workflow events
            async for event in handler.stream_events():
                
                # Filter for text generation events from Ollama
                if isinstance(event, AgentStream):
                    # Replace newlines to prevent breaking the SSE format
                    safe_token = event.delta.replace("\n", "\\n")
                    yield f"data: {safe_token}\n\n"
                    
            # 4. Signal the frontend that the stream is complete
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            # Catch errors (like Ollama timeouts or MCP tool failures)
            # and stream them cleanly to the frontend
            yield f"data: [ERROR] {str(e)}\n\n"

    # Return the generator wrapped in a StreamingResponse
    return StreamingResponse(event_generator(), media_type="text/event-stream")

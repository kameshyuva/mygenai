import json
import redis.asyncio as aioredis
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# Import the celery app instance from your decoupled worker file
from celery_worker import celery_app 

app = FastAPI(title="Decoupled Streaming Agent API")

class ChatRequest(BaseModel):
    prompt: str

@app.post("/api/chat")
async def submit_chat_task(request: ChatRequest):
    # Dispatch the task by name to the Celery worker
    task = celery_app.send_task("run_agent_task", args=[request.prompt])
    
    return {
        "message": "Task submitted successfully",
        "task_id": task.id
    }

@app.get("/api/stream/{task_id}")
async def stream_events(task_id: str):
    """
    Consumes the Redis Pub/Sub channel for the given task_id
    and streams the events to the client using Server-Sent Events (SSE).
    """
    async def event_generator():
        # Connect to Redis asynchronously
        redis_client = await aioredis.from_url("redis://localhost:6379/0")
        pubsub = redis_client.pubsub()
        channel_name = f"stream:{task_id}"
        
        # Subscribe to the specific task's channel
        await pubsub.subscribe(channel_name)
        
        try:
            async for message in pubsub.listen():
                if message['type'] == 'message':
                    # The data is already a JSON string published by the worker
                    raw_data = message['data'].decode('utf-8')
                    parsed_data = json.loads(raw_data)
                    
                    # Yield the data strictly in SSE format
                    yield f"data: {raw_data}\n\n"
                    
                    # Disconnect the stream if the agent signals completion or an error
                    if parsed_data.get("type") in ["done", "error"]:
                        break
        finally:
            # Guarantee cleanup to prevent memory leaks and zombie connections
            await pubsub.unsubscribe(channel_name)
            await redis_client.close()

    return StreamingResponse(event_generator(), media_type="text/event-stream")

import asyncio
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

router = APIRouter()

class TaskRequest(BaseModel):
    query: str
    session_id: str

@router.post("/execute")
async def execute_agent_task(request: Request, payload: TaskRequest):
    redis = request.app.state.redis
    
    # We generate the job ID ahead of time (or let ARQ do it and grab it)
    # Using a predefined job_id makes it easier to immediately return the stream URL
    import uuid
    job_id = str(uuid.uuid4())
    
    # Pass the job_id into the task so the worker knows which channel to publish to
    job = await redis.enqueue_job(
        'run_agent_task',
        query=payload.query,
        session_id=payload.session_id,
        job_id=job_id,
        _job_id=job_id # explicitly set the ARQ job ID
    )
    
    if not job:
        raise HTTPException(status_code=500, detail="Failed to enqueue background job.")
        
    return {"job_id": job_id, "stream_url": f"/api/v1/agents/stream/{job_id}"}

@router.get("/stream/{job_id}")
async def stream_agent_response(request: Request, job_id: str):
    redis_pool = request.app.state.redis

    async def event_generator():
        # Create a dedicated PubSub connection from the pool
        pubsub = redis_pool.pubsub()
        channel_name = f"stream:{job_id}"
        await pubsub.subscribe(channel_name)
        
        try:
            while True:
                # Listen for messages on the channel
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                
                if message is not None:
                    data = message['data'].decode('utf-8')
                    
                    # Check for termination signal
                    if data == "[DONE]":
                        break
                    elif data.startswith("[ERROR]"):
                        yield f"data: {data}\n\n"
                        break
                        
                    # Yield data in standard Server-Sent Events (SSE) format
                    yield f"data: {data}\n\n"
                else:
                    # Give control back to the event loop if no message is ready
                    await asyncio.sleep(0.01)
        finally:
            await pubsub.unsubscribe(channel_name)
            await pubsub.close()

    return StreamingResponse(event_generator(), media_type="text/event-stream")

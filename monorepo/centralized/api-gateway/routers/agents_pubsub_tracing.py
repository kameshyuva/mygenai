import asyncio
import uuid
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from opentelemetry.propagate import inject

router = APIRouter()

class TaskRequest(BaseModel):
    query: str
    session_id: str

@router.post("/execute")
async def execute_agent_task(request: Request, payload: TaskRequest):
    redis = request.app.state.redis
    job_id = str(uuid.uuid4())
    
    # Capture the active OpenTelemetry context from FastAPI
    trace_carrier = {}
    inject(trace_carrier) 
    
    # Pass the carrier along with the standard payload
    job = await redis.enqueue_job(
        'run_agent_task',
        query=payload.query,
        session_id=payload.session_id,
        job_id=job_id,
        trace_carrier=trace_carrier, 
        _job_id=job_id
    )
    
    if not job:
        raise HTTPException(status_code=500, detail="Failed to enqueue background job.")
        
    return {"job_id": job_id, "stream_url": f"/api/v1/agents/stream/{job_id}"}

@router.get("/stream/{job_id}")
async def stream_agent_response(request: Request, job_id: str):
    redis_pool = request.app.state.redis

    async def event_generator():
        pubsub = redis_pool.pubsub()
        channel_name = f"stream:{job_id}"
        await pubsub.subscribe(channel_name)
        
        try:
            while True:
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message is not None:
                    data = message['data'].decode('utf-8')
                    yield data
                    if "event: done" in data:
                        break
                else:
                    await asyncio.sleep(0.01)
        finally:
            await pubsub.unsubscribe(channel_name)
            await pubsub.close()

    return StreamingResponse(event_generator(), media_type="text/event-stream")

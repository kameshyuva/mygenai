# main.py
import uuid
import asyncio
import redis.asyncio as redis
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from arq import create_pool
from arq.connections import RedisSettings

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ARQ pool for enqueuing jobs
    app.state.redis_pool = await create_pool(RedisSettings())
    # Standard Redis client for Pub/Sub listening
    app.state.pubsub_client = redis.Redis.from_url('redis://localhost:6379')
    yield
    await app.state.redis_pool.close()
    await app.state.pubsub_client.aclose()

app = FastAPI(lifespan=lifespan)

class ChatRequest(BaseModel):
    prompt: str

async def redis_stream_generator(pubsub_client: redis.Redis, job_id: str):
    """Subscribes to the Redis channel and yields tokens to the HTTP client."""
    pubsub = pubsub_client.pubsub()
    await pubsub.subscribe(job_id)
    
    try:
        async for message in pubsub.listen():
            # Filter out subscription confirmation messages
            if message['type'] == 'message':
                data = message['data'].decode('utf-8')
                
                # Check for termination flags published by ARQ
                if data == "[DONE]":
                    break
                if data.startswith("[ERROR]"):
                    yield f"Data: Error occurred during agent execution.\n\n"
                    break
                    
                # Yield in Server-Sent Events (SSE) format
                yield f"{data}"
    finally:
        await pubsub.unsubscribe(job_id)
        await pubsub.close()

@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    # Generate a unique ID for the Job and the Pub/Sub channel
    job_id = str(uuid.uuid4())
    
    # 1. Enqueue the task to ARQ
    await app.state.redis_pool.enqueue_job(
        'run_agent_stream', 
        job_id, 
        request.prompt,
        _job_id=job_id # explicitly set the ARQ job ID
    )
    
    # 2. Return the stream, listening to the channel we just created
    return StreamingResponse(
        redis_stream_generator(app.state.pubsub_client, job_id),
        media_type="text/event-stream"
    )

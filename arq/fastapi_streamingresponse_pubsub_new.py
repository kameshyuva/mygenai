import os
import uuid
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import redis.asyncio as redis
from arq import create_pool
from arq.connections import RedisSettings

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.redis_pool = await create_pool(RedisSettings.from_dsn(redis_url))
    app.state.pubsub_client = redis.Redis.from_url(redis_url)
    yield
    await app.state.redis_pool.close()
    await app.state.pubsub_client.aclose()

app = FastAPI(lifespan=lifespan)

class ChatRequest(BaseModel):
    prompt: str

async def redis_stream_generator(pubsub_client: redis.Redis, job_id: str):
    pubsub = pubsub_client.pubsub()
    await pubsub.subscribe(job_id)
    
    try:
        async for message in pubsub.listen():
            if message['type'] == 'message':
                raw_data = message['data'].decode('utf-8')
                
                try:
                    parsed_data = json.loads(raw_data)
                    if parsed_data.get("type") == "AgentComplete":
                        break
                    if parsed_data.get("type") == "AgentError":
                        yield f"data: {raw_data}\n\n"
                        break
                except json.JSONDecodeError:
                    pass 
                
                # Yield the structured JSON string to the client
                yield f"data: {raw_data}\n\n"
                
    finally:
        await pubsub.unsubscribe(job_id)
        await pubsub.close()

@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    job_id = str(uuid.uuid4())
    
    await app.state.redis_pool.enqueue_job(
        'run_agent_stream', 
        job_id, 
        request.prompt,
        _job_id=job_id 
    )
    
    return StreamingResponse(
        redis_stream_generator(app.state.pubsub_client, job_id),
        media_type="text/event-stream"
    )

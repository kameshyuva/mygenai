import logging
from agents.base import build_agent
from arq.connections import RedisSettings

logger = logging.getLogger(__name__)

async def run_agent_task(ctx, query: str, session_id: str, job_id: str) -> str:
    """
    Executes the agent and publishes the streaming response to Redis.
    """
    logger.info(f"Starting agent task for session {session_id}, job {job_id}")
    redis = ctx['redis']
    channel_name = f"stream:{job_id}"
    
    try:
        agent = build_agent(session_id=session_id)
        
        # Use astream_chat to get the streaming response generator
        streaming_response = await agent.astream_chat(query)
        
        full_response = ""
        
        # Iterate over the async generator
        async for token in streaming_response.async_response_gen():
            full_response += token
            # Publish each token to the Redis channel
            await redis.publish(channel_name, token)
            
        # Send a termination signal so the FastAPI gateway knows to close the connection
        await redis.publish(channel_name, "[DONE]")
        
        return full_response
        
    except Exception as e:
        logger.error(f"Agent execution failed: {e}")
        # Ensure we close the stream even on failure
        await redis.publish(channel_name, f"[ERROR] {str(e)}")
        await redis.publish(channel_name, "[DONE]")
        raise e

class WorkerSettings:
    functions = [run_agent_task]
    redis_settings = RedisSettings(host='localhost', port=6379)
    max_jobs = 4 
    job_timeout = 600 

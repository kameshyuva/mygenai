# agents-core/workers/arq_tasks.py
import logging
from agents.base import build_agent
from events.dispatcher import AgentEventDispatcher  # Import from the new file
from arq.connections import RedisSettings

logger = logging.getLogger(__name__)

async def run_agent_task(ctx, query: str, session_id: str, job_id: str) -> str:
    redis = ctx['redis']
    channel_name = f"stream:{job_id}"
    dispatcher = AgentEventDispatcher()
    
    try:
        agent = build_agent(session_id=session_id)
        handler = agent.run(user_msg=query)
        final_response = ""
        
        async for event in handler.stream_events():
            event_name = type(event).__name__
            sse_string = dispatcher.process_event(event_name, event)
            await redis.publish(channel_name, sse_string)
            
            if event_name == "AgentOutput":
                final_response = str(getattr(event, "response", ""))

        await redis.publish(channel_name, "event: done\ndata: {}\n\n")
        return final_response
        
    except Exception as e:
        logger.error(f"Agent execution failed: {e}")
        await redis.publish(channel_name, dispatcher.process_event("Error", {"detail": str(e)}))
        await redis.publish(channel_name, "event: done\ndata: {}\n\n")
        raise e

class WorkerSettings:
    functions = [run_agent_task]
    redis_settings = RedisSettings(host='localhost', port=6379)
    max_jobs = 4 
    job_timeout = 600 

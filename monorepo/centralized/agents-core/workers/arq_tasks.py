import logging
from agents.base import build_agent
from arq.connections import RedisSettings

logger = logging.getLogger(__name__)

async def run_agent_task(ctx, query: str, session_id: str) -> str:
    """
    The asynchronous task executed by the ARQ worker.
    """
    logger.info(f"Starting agent task for session {session_id}")
    
    try:
        # Build the specific agent state
        agent = build_agent(session_id=session_id)
        
        # Execute the multi-step reasoning and tool calling process
        response = await agent.achat(query)
        
        # In a real environment, you might emit this via SSE to the frontend 
        # before returning the final string to the ARQ result store.
        return str(response)
        
    except Exception as e:
        logger.error(f"Agent execution failed: {e}")
        raise e

class WorkerSettings:
    """
    ARQ configuration for starting the background worker process.
    """
    functions = [run_agent_task]
    redis_settings = RedisSettings(host='localhost', port=6379)
    
    # Limit concurrency to prevent thread starvation on CPU-bound local infrastructure
    max_jobs = 4 
    job_timeout = 600  # Allow up to 10 minutes for heavy loops

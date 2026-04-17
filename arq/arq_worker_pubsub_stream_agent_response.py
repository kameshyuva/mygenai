import os
import asyncio
import redis.asyncio as redis
from arq import Retry, func
from agent import MyCustomAgent 

class AgentTaskQueue:
    @staticmethod
    async def run_agent_stream(ctx, job_id: str, prompt: str):
        current_attempt = ctx['job_try']
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        redis_client = redis.Redis.from_url(redis_url)
        
        try:
            agent_instance = MyCustomAgent()
            
            # 1. Grab your stream handler
            handler = agent_instance.stream_handler()
            
            # 2. Schedule the agent's async run method as a concurrent task.
            # This starts the execution immediately but yields control back to 
            # the ARQ event loop so it doesn't block.
            run_task = asyncio.create_task(agent_instance.run(prompt))
            
            # 3. Asynchronously iterate over the tokens emitted by the handler.
            # (Assuming your handler implements an async generator `__aiter__`)
            async for token in handler: 
                await redis_client.publish(job_id, token)
                
            # 4. Await the execution task to ensure it finished cleanly and 
            # to propagate any exceptions that occurred during the run.
            await run_task
            
            # 5. Signal the FastAPI endpoint that the stream is complete
            await redis_client.publish(job_id, "[DONE]")
            
        except Exception as e:
            # Catch network timeouts, LLM errors, or tool failures
            if current_attempt < 4:
                backoff_delay = current_attempt * 10
                print(f"Agent task failed: {e}. Retrying in {backoff_delay}s...")
                raise Retry(defer=backoff_delay)
            else:
                await redis_client.publish(job_id, f"[ERROR] Task failed permanently: {str(e)}")
                raise e 
        finally:
            await redis_client.aclose()

class WorkerSettings:
    functions = [
        func(AgentTaskQueue.run_agent_stream, max_tries=4)
    ]
    job_timeout = 600

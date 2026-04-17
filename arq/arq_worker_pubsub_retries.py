import os
import redis.asyncio as redis
from arq import Retry, func
from arq.connections import RedisSettings
from agent import MyCustomAgent

class AgentTaskQueue:
    @staticmethod
    async def run_agent_stream(ctx, job_id: str, prompt: str):
        """Background task that runs the agent and publishes tokens."""
        current_attempt = ctx['job_try']
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        redis_client = redis.Redis.from_url(redis_url)
        
        try:
            # 1. Initialize the agent and run the prompt
            agent_instance = MyCustomAgent()
            response = await agent_instance.run_stream(prompt)
            
            # 2. Publish streamed tokens immediately to the Redis channel
            async for token in response.async_response_gen():
                await redis_client.publish(job_id, token)
                
            # 3. Publish termination flag
            await redis_client.publish(job_id, "[DONE]")
            
        except Exception as e:
            # 4. Implement exponential backoff for tool/LLM failures
            if current_attempt < 4:
                backoff_delay = current_attempt * 10
                print(f"Agent task failed: {e}. Retrying in {backoff_delay}s...")
                raise Retry(defer=backoff_delay)
            else:
                # 5. Max retries exceeded; report the final error to the client
                await redis_client.publish(job_id, f"[ERROR] Task failed permanently: {str(e)}")
                raise e 
        finally:
            # Ensure the connection is cleanly closed
            await redis_client.aclose()

# Global settings required by the ARQ worker process
class WorkerSettings:
    functions = [
        # Wrap the function to define a specific max_tries limit for this task
        func(AgentTaskQueue.run_agent_stream, max_tries=4)
    ]
    
    redis_settings = RedisSettings.from_dsn(os.getenv("REDIS_URL", "redis://localhost:6379"))
    
    # High timeout allowance for I/O bound local model execution
    job_timeout = 600 

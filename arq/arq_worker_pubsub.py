# arq_worker.py
import redis.asyncio as redis
from agent import MyCustomAgent

class AgentTaskQueue:
    @staticmethod
    async def run_agent_stream(ctx, job_id: str, prompt: str):
        """
        The background task. Executes the agent and publishes tokens to Redis Pub/Sub.
        """
        # Connect to Redis for Pub/Sub (Standard redis-py async client)
        redis_client = redis.Redis.from_url('redis://localhost:6379')
        
        try:
            # 1. Initialize your existing agent logic
            agent_instance = MyCustomAgent()
            
            # 2. Start the streaming execution
            response = await agent_instance.run_stream(prompt)
            
            # 3. Publish tokens as they arrive from Ollama/MCP
            async for token in response.async_response_gen():
                await redis_client.publish(job_id, token)
                
            # 4. Signal that the stream is complete
            await redis_client.publish(job_id, "[DONE]")
            
        except Exception as e:
            await redis_client.publish(job_id, f"[ERROR] {str(e)}")
            
        finally:
            await redis_client.aclose()

# ARQ expects a WorkerSettings class/dict at the module level
class WorkerSettings:
    functions = [AgentTaskQueue.run_agent_stream]
    job_timeout = 600 # 10 minutes, adjust based on complex MCP tool calls

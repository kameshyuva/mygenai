import asyncio
import json
import redis.asyncio as aioredis
from celery import Celery

# Import your pristine agent class
from agent import MCPStreamingAgent

class AgentTaskWorker:
    def __init__(self, broker_url: str = "redis://localhost:6379/0"):
        self.redis_url = broker_url
        self.app = Celery("agent_tasks", broker=broker_url, backend=broker_url)
        self._register_tasks()

    def _register_tasks(self):
        # Bind the task to the Celery app instance
        @self.app.task(bind=True, name="run_agent_task")
        def run_agent_task(task_instance, prompt: str):
            task_instance.update_state(state='PROCESSING')
            task_id = task_instance.request.id
            
            # Run the async bridge synchronously for Celery
            result = asyncio.run(self._async_agent_runner(prompt, task_id))
            return {"result": result}
            
    async def _async_agent_runner(self, prompt: str, task_id: str):
        channel_name = f"stream:{task_id}"
        redis_client = await aioredis.from_url(self.redis_url)
        
        try:
            # Instantiate your decoupled agent
            agent = MCPStreamingAgent()
            
            # Consume the agent's agnostic generator and publish to Redis
            async for event_data in agent.stream_run(prompt):
                await redis_client.publish(channel_name, json.dumps(event_data))
                
            return "Streaming completed successfully."
            
        finally:
            await redis_client.close()

# Initialize the worker singleton so the Celery CLI can find it
worker_instance = AgentTaskWorker()
celery_app = worker_instance.app

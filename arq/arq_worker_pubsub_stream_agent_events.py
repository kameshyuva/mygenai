import os
import json
import redis.asyncio as redis
from arq import Retry, func
from arq.connections import RedisSettings
from agent import MyCustomAgent 

def serialize_agent_event(event) -> str:
    """Converts complex LlamaIndex agent events into structured JSON."""
    event_type = type(event).__name__
    payload = {"type": event_type}
    
    try:
        if event_type == "AgentInput":
            payload["content"] = getattr(event, "input", str(event))
        elif event_type == "AgentStream":
            payload["delta"] = getattr(event, "delta", "")
        elif event_type == "ToolCall":
            payload["tool_name"] = getattr(event, "tool_name", "unknown_tool")
            payload["tool_kwargs"] = getattr(event, "tool_kwargs", {})
        else:
            payload["content"] = str(event)
    except Exception as e:
        payload = {"type": "SerializationError", "content": f"Parse failure: {e}"}

    return json.dumps(payload)

class AgentTaskQueue:
    @staticmethod
    async def run_agent_stream(ctx, job_id: str, prompt: str):
        current_attempt = ctx['job_try']
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        redis_client = redis.Redis.from_url(redis_url)
        
        try:
            agent_instance = MyCustomAgent()
            
            # 1. Execute the run method to obtain the handler
            handler = agent_instance.run(prompt)
            
            # 2. Iterate asynchronously over the specific framework events
            async for event in handler.stream_events():
                json_payload = serialize_agent_event(event)
                await redis_client.publish(job_id, json_payload)
                
            # 3. Publish termination signal after final guardrail check
            done_payload = json.dumps({"type": "AgentComplete", "content": "[DONE]"})
            await redis_client.publish(job_id, done_payload)
            
        except Exception as e:
            if current_attempt < 4:
                backoff_delay = current_attempt * 10
                print(f"Task failed: {e}. Retrying in {backoff_delay}s...")
                raise Retry(defer=backoff_delay)
            else:
                error_payload = json.dumps({"type": "AgentError", "content": str(e)})
                await redis_client.publish(job_id, error_payload)
                raise e 
        finally:
            await redis_client.aclose()

class WorkerSettings:
    functions = [
        func(AgentTaskQueue.run_agent_stream, max_tries=4)
    ]
    redis_settings = RedisSettings.from_dsn(os.getenv("REDIS_URL", "redis://localhost:6379"))
    job_timeout = 600

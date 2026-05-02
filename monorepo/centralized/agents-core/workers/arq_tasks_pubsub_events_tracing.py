import logging
from agents.base import build_agent
from events.dispatcher import AgentEventDispatcher
from arq.connections import RedisSettings
from shared_libs.telemetry import setup_phoenix_tracing
from openinference.instrumentation.llama_index import LlamaIndexInstrumentor
from opentelemetry import context as otel_context
from opentelemetry.propagate import extract

logger = logging.getLogger(__name__)

async def worker_startup(ctx):
    """ARQ lifecycle hook to initialize tracing before processing jobs."""
    setup_phoenix_tracing(project_name="agents-worker")
    LlamaIndexInstrumentor().instrument()
    logger.info("Agent Worker OpenInference tracing initialized.")

async def run_agent_task(ctx, query: str, session_id: str, job_id: str, trace_carrier: dict = None) -> str:
    redis = ctx['redis']
    channel_name = f"stream:{job_id}"
    dispatcher = AgentEventDispatcher()
    
    # Rehydrate the distributed trace context
    token = None
    if trace_carrier:
        parent_context = extract(trace_carrier)
        token = otel_context.attach(parent_context)
        
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
        
    finally:
        # Clean up the trace context so it does not bleed into the next queue job
        if token:
            otel_context.detach(token)

class WorkerSettings:
    functions = [run_agent_task]
    on_startup = worker_startup
    redis_settings = RedisSettings(host='redis', port=6379)
    max_jobs = 4 
    job_timeout = 600

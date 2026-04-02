import atexit
from contextlib import asynccontextmanager
from fastapi import FastAPI
from pydantic import BaseModel
from opentelemetry import trace

import phoenix as px
from openinference.instrumentation.llama_index import LlamaIndexInstrumentor
from phoenix.otel import register
from openinference.semconv.trace import SpanAttributes

from llama_index.core.agent import FunctionAgent
from llama_index.core.tools import FunctionTool
from llama_index.llms.ollama import Ollama

# ==========================================
# 1. TRACING MANAGER
# ==========================================
class PhoenixTracingManager:
    """Manages Arize Phoenix tracing with Batch processing and safe reloads."""
    _is_instrumented = False
    _session = None
    _tracer_provider = None

    @classmethod
    def enable_tracing(cls, project_name: str = "fastapi-agent-tracing", port: int = 6006):
        if cls._session is None:
            cls._session = px.launch_app(port=port)
            print(f"[Tracing] Phoenix dashboard is live at: {cls._session.url}")

        if not cls._is_instrumented:
            endpoint = f"http://localhost:{port}/v1/traces"
            
            # Use BatchSpanProcessor to prevent blocking the main FastAPI thread
            cls._tracer_provider = register(
                project_name=project_name,
                endpoint=endpoint,
                batch=True 
            )
            
            try:
                # Force clear lingering instrumentation from Uvicorn hot-reloads
                LlamaIndexInstrumentor().uninstrument()
                
                LlamaIndexInstrumentor().instrument(tracer_provider=cls._tracer_provider)
                cls._is_instrumented = True
                print(f"[Tracing] Batch OpenTelemetry instrumentation enabled for project: '{project_name}'")
            except Exception as e:
                print(f"[Tracing] Note: {str(e)}")

    @classmethod
    def shutdown(cls):
        """Flushes remaining spans to Phoenix on server exit."""
        if cls._tracer_provider:
            print("[Tracing] Flushing remaining spans to Phoenix before exit...")
            cls._tracer_provider.shutdown()

# ==========================================
# 2. AGENT DEFINITION
# ==========================================
def multiply_numbers(a: int, b: int) -> int:
    """Multiplies two integers and returns the result."""
    return a * b

multiply_tool = FunctionTool.from_defaults(fn=multiply_numbers)

# Initialize Ollama synchronously to prevent context leakage and streaming bugs
llm = Ollama(model="llama3", request_timeout=120.0)

# FunctionAgent is used for native tool calling and stable tracing structures
agent = FunctionAgent.from_tools(
    [multiply_tool], 
    llm=llm, 
    verbose=True
)

# ==========================================
# 3. FASTAPI LIFESPAN & APP
# ==========================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs once on startup
    PhoenixTracingManager.enable_tracing(project_name="fastapi-agent-tracing")
    yield
    # Runs once on shutdown
    PhoenixTracingManager.shutdown()

app = FastAPI(lifespan=lifespan)

class ChatRequest(BaseModel):
    query: str

# ==========================================
# 4. API ROUTES
# ==========================================
@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    # 1. Grab the generic HTTP root span created by FastAPI
    current_span = trace.get_current_span()
    
    # 2. Hijack the span to inject OpenInference AI labels
    if current_span and current_span.is_recording():
        # Forces Phoenix to categorize this route as a 'CHAIN' instead of 'unknown'
        current_span.set_attribute(SpanAttributes.OPENINFERENCE_SPAN_KIND, "CHAIN")
        current_span.set_attribute(SpanAttributes.INPUT_VALUE, request.query)

    # 3. Execute the agent synchronously (blocks stream to guarantee valid REST response)
    response = agent.chat(request.query)
    
    # 4. Inject the final agent response back into the root span
    if current_span and current_span.is_recording():
        current_span.set_attribute(SpanAttributes.OUTPUT_VALUE, str(response.response))
        
    return {"response": str(response.response)}

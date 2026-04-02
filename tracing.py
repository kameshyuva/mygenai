
#pip install arize-phoenix openinference-instrumentation-llama-index llama-index llama-index-llms-ollama


import atexit
import phoenix as px
from openinference.instrumentation.llama_index import LlamaIndexInstrumentor
from phoenix.otel import register

class PhoenixTracingManager:
    """
    A singleton-style manager to handle Arize Phoenix tracing initialization 
    for LlamaIndex agents using the recommended BatchSpanProcessor.
    """
    _is_instrumented = False
    _session = None
    _tracer_provider = None

    @classmethod
    def enable_tracing(cls, project_name: str = "llama-agent-tracing", port: int = 6006):
        """
        Launches the Phoenix app and registers the LlamaIndex instrumentor
        using asynchronous batch processing.
        """
        # 1. Launch the Phoenix app
        if cls._session is None:
            cls._session = px.launch_app(port=port)
            print(f"[Tracing] Phoenix dashboard is live at: {cls._session.url}")

        # 2. Instrument LlamaIndex with Batch Processing
        if not cls._is_instrumented:
            endpoint = f"http://localhost:{port}/v1/traces"
            
            # batch=True forces OpenTelemetry to use the BatchSpanProcessor
            cls._tracer_provider = register(
                project_name=project_name,
                endpoint=endpoint,
                batch=True 
            )
            
            LlamaIndexInstrumentor().instrument(tracer_provider=cls._tracer_provider)
            cls._is_instrumented = True
            
            # Register the shutdown hook to flush the batch queue on exit
            atexit.register(cls.shutdown)
            
            print(f"[Tracing] Batch OpenTelemetry instrumentation enabled for project: '{project_name}'")
        else:
            print(f"[Tracing] Instrumentation already active. Logging to project: '{project_name}'")
            
        return cls._session

    @classmethod
    def shutdown(cls):
        """Flushes remaining spans in the BatchSpanProcessor queue."""
        if cls._tracer_provider:
            print("[Tracing] Flushing remaining spans to Phoenix before exit...")
            cls._tracer_provider.shutdown()

    @classmethod
    def get_dashboard_url(cls) -> str:
        """Returns the active Phoenix dashboard URL, if running."""
        return cls._session.url if cls._session else "Phoenix is not running."

# Add this inside your PhoenixTracingManager class in tracing_manager.py

    @classmethod
    def get_tracer(cls, module_name: str):
        """Returns a Phoenix-aware tracer for manual span decorators."""
        if not cls._tracer_provider:
            raise RuntimeError("Tracing not initialized. Call enable_tracing() first.")
        return cls._tracer_provider.get_tracer(module_name)


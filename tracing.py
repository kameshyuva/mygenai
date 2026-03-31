
#pip install arize-phoenix openinference-instrumentation-llama-index llama-index llama-index-llms-ollama

import phoenix as px
from openinference.instrumentation.llama_index import LlamaIndexInstrumentor
from phoenix.otel import register

class PhoenixTracingManager:
    """
    A singleton-style manager to handle Arize Phoenix tracing initialization 
    for LlamaIndex agents. Ensures instrumentation only happens once.
    """
    _is_instrumented = False
    _session = None

    @classmethod
    def enable_tracing(cls, project_name: str = "llama-agent-tracing", port: int = 6006):
        """
        Launches the Phoenix app (if not already running) and registers 
        the LlamaIndex instrumentor.
        """
        # 1. Launch the Phoenix app only once per process
        if cls._session is None:
            cls._session = px.launch_app(port=port)
            print(f"[Tracing] Phoenix dashboard is live at: {cls._session.url}")

        # 2. Instrument LlamaIndex only once
        if not cls._is_instrumented:
            endpoint = f"http://localhost:{port}/v1/traces"
            
            tracer_provider = register(
                project_name=project_name,
                endpoint=endpoint
            )
            
            LlamaIndexInstrumentor().instrument(tracer_provider=tracer_provider)
            cls._is_instrumented = True
            print(f"[Tracing] OpenTelemetry instrumentation enabled for project: '{project_name}'")
        else:
            print(f"[Tracing] Instrumentation already active. Logging to project: '{project_name}'")
            
        return cls._session

    @classmethod
    def get_dashboard_url(cls) -> str:
        """Returns the active Phoenix dashboard URL, if running."""
        return cls._session.url if cls._session else "Phoenix is not running."

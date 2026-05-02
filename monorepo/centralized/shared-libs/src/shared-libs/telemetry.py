import os
from phoenix.otel import register

def setup_phoenix_tracing(project_name: str):
    """
    Initializes OpenTelemetry tracing routed to Arize Phoenix.
    """
    # Pulls the endpoint from the docker-compose environment variables
    endpoint = os.environ.get("PHOENIX_COLLECTOR_ENDPOINT", "http://localhost:4317")
    
    # Registers the TracerProvider with Phoenix-aware defaults
    tracer_provider = register(
        project_name=project_name,
        endpoint=f"{endpoint}/v1/traces"
    )
    return tracer_provider

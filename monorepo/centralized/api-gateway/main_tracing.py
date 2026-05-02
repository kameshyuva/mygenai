import contextlib
from fastapi import FastAPI
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from arq import create_pool
from arq.connections import RedisSettings
from routers.agents import router as agents_router
from shared_libs.telemetry import setup_phoenix_tracing

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.redis = await create_pool(RedisSettings(host='redis', port=6379))
    yield
    app.state.redis.close()
    await app.state.redis.wait_closed()

app = FastAPI(
    title="Centralized Agent API Gateway",
    lifespan=lifespan
)

# Initialize Phoenix tracing for the ingress layer
setup_phoenix_tracing(project_name="api-gateway")
FastAPIInstrumentor.instrument_app(app)

app.include_router(agents_router, prefix="/api/v1/agents", tags=["Agents"])

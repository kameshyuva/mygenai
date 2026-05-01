import contextlib
from fastapi import FastAPI
from arq import create_pool
from arq.connections import RedisSettings
from routers.agents import router as agents_router

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    # Establish the Redis connection pool for ARQ on startup
    app.state.redis = await create_pool(RedisSettings(host='localhost', port=6379))
    yield
    # Cleanly close the pool on shutdown
    app.state.redis.close()
    await app.state.redis.wait_closed()

app = FastAPI(
    title="Centralized Agent API Gateway",
    description="Ingress routing and ARQ task dispatching.",
    lifespan=lifespan
)

# Mount the agent task router
app.include_router(agents_router, prefix="/api/v1/agents", tags=["Agents"])

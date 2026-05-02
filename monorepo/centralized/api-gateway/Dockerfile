FROM python:3.11-slim-bookworm

# Install uv directly from the official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
WORKDIR /app

# 1. Copy the universal lockfile and workspace configurations
COPY uv.lock pyproject.toml ./

# 2. Copy the pyproject.toml files needed for THIS specific package
COPY api-gateway/pyproject.toml api-gateway/
COPY shared-libs/pyproject.toml shared-libs/

# 3. Sync dependencies without source code to maximize Docker layer caching
RUN uv sync --frozen --no-install-project --package api-gateway

# 4. Copy the actual source code
COPY api-gateway/ api-gateway/
COPY shared-libs/ shared-libs/

# 5. Install the project
RUN uv sync --frozen --package api-gateway

# 6. Execute the FastAPI server
CMD ["uv", "run", "--project", "api-gateway", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--app-dir", "api-gateway"]

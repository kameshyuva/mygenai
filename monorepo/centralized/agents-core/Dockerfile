FROM python:3.11-slim-bookworm

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
WORKDIR /app

# 1. Copy the universal lockfile and workspace configurations
COPY uv.lock pyproject.toml ./

# 2. Copy the pyproject.toml files needed for THIS specific package
COPY agents-core/pyproject.toml agents-core/
COPY shared-libs/pyproject.toml shared-libs/

# 3. Sync dependencies without source code (maximizes cache)
RUN uv sync --frozen --no-install-project --package agents-core

# 4. Copy the actual source code
COPY agents-core/ agents-core/
COPY shared-libs/ shared-libs/

# 5. Install the project
RUN uv sync --frozen --package agents-core

# Execute the ARQ worker using the uv environment
CMD ["uv", "run", "--project", "agents-core", "arq", "workers.arq_tasks.WorkerSettings"]

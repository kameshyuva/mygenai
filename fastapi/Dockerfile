# 1. Use a lightweight, official Python base image
FROM python:3.11-slim

# 2. Copy the compiled `uv` binary directly from Astral's official image
# This is much faster and cleaner than installing it via pip/curl
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# 3. Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # Optional: Tell uv to compile bytecode for faster startup times
    UV_COMPILE_BYTECODE=1 

WORKDIR /app

# 4. Copy dependency files first for layer caching
# If using pyproject.toml and uv.lock:
# COPY pyproject.toml uv.lock ./
# If using requirements.txt:
COPY requirements.txt ./

# 5. Install dependencies
# 'uv venv' creates the .venv directory
# 'uv pip install' installs the packages into that .venv
RUN uv venv && uv pip install -r requirements.txt
# (If using pyproject.toml, simply run: RUN uv sync --frozen)

# 6. Copy the application code
COPY ./app /app/app

# 7. Create a non-root user for security
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser /app
USER appuser

EXPOSE 8000

# 8. Start Gunicorn using `uv run` to ensure it uses the virtual environment
CMD ["uv", "run", "gunicorn", "app.main:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]

# Use an official lightweight Python image
FROM python:3.11-slim

# Prevent Python from writing pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Copy the uv binary directly from the official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Install dependencies using uv for significantly faster builds
COPY requirements.txt .
RUN uv pip install --system --no-cache -r requirements.txt

# Copy the rest of your application code
COPY . .

# Default command uses Gunicorn with Uvicorn workers
CMD ["gunicorn", "main:app", "--workers", "2", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]

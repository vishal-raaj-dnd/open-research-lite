# syntax=docker/dockerfile:1
FROM python:3.11-slim

# Prevent Python from writing .pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8 \
    TERM=xterm-256color

# Install system dependencies (curl for healthchecks / troubleshooting)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Set up working directory for reports and project files
WORKDIR /workspace

# Copy build definition first to leverage Docker layer caching
COPY pyproject.toml README.md /app/
COPY src/ /app/src/

# Install open-research-lite and all required dependencies in container
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir "/app"

# Default volume mount point so generated reports persist on host
VOLUME ["/workspace"]

# Interactive entrypoint launching the crimson research wizard
ENTRYPOINT ["open-research"]
CMD []

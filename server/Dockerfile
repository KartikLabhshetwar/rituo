# Use Python 3.12 slim image as base
FROM python:3.12-slim

# Set environment variables for optimal Python runtime
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV PIP_NO_CACHE_DIR=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install UV package manager for faster dependency management
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

# Copy dependency files first for better caching
COPY pyproject.toml uv.lock ./

# Install Python dependencies using UV
RUN uv sync --frozen --no-dev

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash --uid 1000 rituo && \
    chown -R rituo:rituo /app
USER rituo

# Expose ports
# Port 8000 for FastAPI REST API
# Port 8001 for MCP Server
EXPOSE 8000 8001

# Health check for container orchestration
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Use exec form for better signal handling
CMD ["uv", "run", "app.py"]

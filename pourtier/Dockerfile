# ============================================
# Multi-stage Dockerfile for Pourtier
# Uses Private PyPI Registry for shared package
# ============================================

# ============================================
# Build stage
# ============================================
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pourtier/pyproject.toml ./
COPY pourtier/src/ ./src/

# Install dependencies (shared will be fetched from PyPI registry)
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --user --no-cache-dir \
    --extra-index-url http://172.17.0.1:9001/simple/ \
    --trusted-host 172.17.0.1 \
    .

# ============================================
# Development stage (with hot reload)
# ============================================
FROM python:3.11-slim AS development

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local

# Update PATH and set Python env vars
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV ENV=development

# Copy application code
COPY pourtier/ .

# Install in editable mode for development
RUN pip install --no-cache-dir \
    --extra-index-url http://172.17.0.1:9001/simple/ \
    --trusted-host 172.17.0.1 \
    -e ".[dev]"

# Expose port (dynamic, will be set via docker-compose)
EXPOSE 8000 9000 7000

# Health check (uses API_PORT env var with fallback)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${API_PORT:-8000}/health || exit 1

# Run with Python module which reads port from settings
CMD ["python", "-m", "pourtier.main"]

# ============================================
# Production stage (optimized)
# ============================================
FROM python:3.11-slim AS production

# Create non-root user
RUN useradd -m -u 1000 -s /bin/bash pourtier && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /root/.local /home/pourtier/.local

# Copy application code
COPY --chown=pourtier:pourtier pourtier/config/ ./config/
COPY --chown=pourtier:pourtier pourtier/src/ ./src/
COPY --chown=pourtier:pourtier pourtier/scripts/ ./scripts/

# Copy Alembic migrations
COPY --chown=pourtier:pourtier pourtier/alembic/ ./alembic/
COPY --chown=pourtier:pourtier pourtier/alembic.ini ./alembic.ini

# Switch to non-root user
USER pourtier

# Update PATH and set Python env vars
ENV PATH=/home/pourtier/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV ENV=production

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${API_PORT:-8000}/health || exit 1

# Run with Python module which reads port from settings
CMD ["python", "-m", "pourtier.main"]

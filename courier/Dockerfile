# ============================================
# Multi-stage Dockerfile for Courier
# Uses Private PyPI Registry for shared package
# Clean Architecture Implementation
# Build context: courier/ directory
# ============================================

# ============================================
# Stage 1: Python build
# ============================================
FROM python:3.11-slim AS python-builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy courier package files
COPY pyproject.toml ./
COPY src/ ./src/

# Install courier (shared will be fetched from PyPI registry)
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --user --no-cache-dir \
    --extra-index-url http://172.17.0.1:9001/simple/ \
    --trusted-host 172.17.0.1 \
    .

# ============================================
# Stage 2: Development
# ============================================
FROM python:3.11-slim AS development

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=python-builder /root/.local /root/.local

# Update PATH
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Copy application code
COPY . .

# Install in editable mode for development
RUN pip install --no-cache-dir \
    --extra-index-url http://172.17.0.1:9001/simple/ \
    --trusted-host 172.17.0.1 \
    -e ".[dev]"

# Create logs directory
RUN mkdir -p logs

# Expose port (development uses 9765, but E2E tests override with PORT env var)
EXPOSE 9765

# Health check (uses PORT env var if set, defaults to 9765)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${PORT:-9765}/health || exit 1

# Run development (using main.py)
CMD ["python", "-m", "courier.main"]

# ============================================
# Stage 3: Production
# ============================================
FROM python:3.11-slim AS production

# Create non-root user
RUN useradd -m -u 1000 -s /bin/bash courier_user && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy Python packages from builder
COPY --from=python-builder /root/.local /home/courier_user/.local

# Copy application code
COPY --chown=courier_user:courier_user config/ ./config/
COPY --chown=courier_user:courier_user src/ ./src/

# Create logs directory with proper permissions
RUN mkdir -p /app/logs && \
    chown -R courier_user:courier_user /app/logs && \
    mkdir -p /home/courier_user/logs && \
    chown -R courier_user:courier_user /home/courier_user/logs

# Switch to non-root user
USER courier_user

# Update PATH
ENV PATH=/home/courier_user/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Expose port (production uses 8765)
EXPOSE 8765

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8765/health || exit 1

# Run production server (using main.py)
CMD ["python", "-m", "courier.main"]

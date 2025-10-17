# ============================================
# Multi-stage Dockerfile for Courier
# Uses Private PyPI Registry for shared package
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
COPY courier/pyproject.toml ./
COPY courier/src/ ./src/

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
COPY courier/ .

# Install in editable mode for development
RUN pip install --no-cache-dir \
    --extra-index-url http://172.17.0.1:9001/simple/ \
    --trusted-host 172.17.0.1 \
    -e ".[dev]"

# Create logs directory
RUN mkdir -p logs

# Expose port
EXPOSE 8766

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8766/health || exit 1

# Run development
CMD ["python", "-m", "courier.broker"]

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
COPY --chown=courier_user:courier_user courier/config/ ./config/
COPY --chown=courier_user:courier_user courier/src/ ./src/

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

# Expose port
EXPOSE 8765

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8765/health || exit 1

# Run production server
CMD ["python", "-m", "courier.broker"]

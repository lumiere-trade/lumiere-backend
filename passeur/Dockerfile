# ============================================
# Multi-stage Dockerfile for Passeur
# Python + Node.js bridge server with supervisord
# Uses Private PyPI Registry for shared package
# ============================================

# ============================================
# Stage 1: Node.js dependencies
# ============================================
FROM node:18-alpine AS node-builder

WORKDIR /app/bridge
COPY passeur/bridge/package*.json ./
RUN npm ci
COPY passeur/bridge/ ./

# ============================================
# Stage 2: Python build stage
# ============================================
FROM python:3.11-slim AS python-builder

WORKDIR /build

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

COPY passeur/pyproject.toml ./
COPY passeur/src/ ./src/

# Install system-wide (not --user)
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir \
    --extra-index-url http://172.17.0.1:10001/simple/ \
    --trusted-host 172.17.0.1 \
    .

# ============================================
# Stage 3: Development stage (with hot reload)
# ============================================
FROM python:3.11-slim AS development

WORKDIR /app

# Install Node.js, supervisor, and curl
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    supervisor \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder (system-wide installation)
COPY --from=python-builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=python-builder /usr/local/bin /usr/local/bin

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV NODE_ENV=development

# Copy bridge with node_modules
COPY --from=node-builder /app/bridge ./bridge

# Copy application code
COPY passeur/config/ ./config/
COPY passeur/src/ ./src/
COPY passeur/tests/ ./tests/
COPY passeur/pyproject.toml ./pyproject.toml

# Copy supervisord configuration
COPY passeur/supervisord.conf /etc/supervisor/conf.d/passeur.conf

# Install passeur as editable for development
RUN pip install --no-cache-dir \
    --extra-index-url http://172.17.0.1:10001/simple/ \
    --trusted-host 172.17.0.1 \
    -e ".[dev]"

# Expose Python API port (bridge is internal)
EXPOSE 7766

HEALTHCHECK --interval=10s --timeout=5s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:7766/health || exit 1

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/passeur.conf"]

# ============================================
# Stage 4: Production stage (optimized)
# ============================================
FROM python:3.11-slim AS production

# Create non-root user
RUN useradd -m -u 1000 -s /bin/bash passeur

# Install Node.js, supervisor, and curl
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    supervisor \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy Python packages from builder (system-wide)
COPY --from=python-builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=python-builder /usr/local/bin /usr/local/bin

# Copy bridge
COPY --from=node-builder /app/bridge ./bridge

# Copy application code
COPY --chown=passeur:passeur passeur/config/ ./config/
COPY --chown=passeur:passeur passeur/src/ ./src/

# Copy supervisord configuration
COPY passeur/supervisord.conf /etc/supervisor/conf.d/passeur.conf

USER passeur
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV NODE_ENV=production

# Expose Python API port (bridge is internal)
EXPOSE 8766

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8766/health || exit 1

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/passeur.conf"]

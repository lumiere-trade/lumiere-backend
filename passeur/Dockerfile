# ============================================
# Multi-stage Dockerfile for Passeur
# Python + Node.js bridge server
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

RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --user --no-cache-dir \
    --extra-index-url http://172.17.0.1:10001/simple/ \
    --trusted-host 172.17.0.1 \
    .

# ============================================
# Stage 3: Development stage (with hot reload)
# ============================================
FROM python:3.11-slim AS development

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

COPY --from=python-builder /root/.local /root/.local

ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV NODE_ENV=development

# CRITICAL: Copy bridge with node_modules FIRST
COPY --from=node-builder /app/bridge ./bridge

# Then copy everything else EXCEPT bridge (to avoid overwriting)
COPY passeur/config/ ./config/
COPY passeur/src/ ./src/
COPY passeur/tests/ ./tests/
COPY passeur/pyproject.toml ./pyproject.toml

# Install passeur as editable for development
RUN pip install --no-cache-dir \
    --extra-index-url http://172.17.0.1:10001/simple/ \
    --trusted-host 172.17.0.1 \
    -e ".[dev]"

EXPOSE 8766

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8766/health || exit 1

CMD ["npm", "run", "dev", "--prefix", "bridge"]

# ============================================
# Stage 4: Production stage (optimized)
# ============================================
FROM python:3.11-slim AS production

RUN useradd -m -u 1000 -s /bin/bash passeur && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=python-builder /root/.local /home/passeur/.local
COPY --from=node-builder /app/bridge ./bridge

COPY --chown=passeur:passeur passeur/config/ ./config/
COPY --chown=passeur:passeur passeur/src/ ./src/

USER passeur

ENV PATH=/home/passeur/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV NODE_ENV=production

EXPOSE 8766

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8766/health || exit 1

CMD ["node", "bridge/server.js"]

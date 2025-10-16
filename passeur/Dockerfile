# ============================================
# Multi-stage Dockerfile for Passeur
# Python + Node.js bridge server
# ============================================

# ============================================
# Stage 1: Node.js dependencies
# ============================================
FROM node:18-alpine AS node-builder

WORKDIR /app/bridge

# Install Node.js dependencies
COPY bridge/package*.json ./
RUN npm ci --only=production

# Copy bridge source code
COPY bridge/ ./

# ============================================
# Stage 2: Python build stage
# ============================================
FROM python:3.11-slim AS python-builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy Python package files
COPY pyproject.toml ./
COPY src/ ./src/

# Install Python package
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --user --no-cache-dir .

# ============================================
# Stage 3: Development stage (with hot reload)
# ============================================
FROM python:3.11-slim AS development

WORKDIR /app

# Install runtime dependencies including Node.js
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=python-builder /root/.local /root/.local

# Copy Node.js dependencies and bridge code
COPY --from=node-builder /app/bridge ./bridge

# Update PATH
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV NODE_ENV=development

# Copy application code
COPY . .

# Expose bridge port
EXPOSE 8766

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8766/health || exit 1

# Run with nodemon for auto-reload in development
CMD ["npm", "run", "dev", "--prefix", "bridge"]

# ============================================
# Stage 4: Production stage (optimized)
# ============================================
FROM python:3.11-slim AS production

# Create non-root user
RUN useradd -m -u 1000 -s /bin/bash passeur && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy Python packages from builder
COPY --from=python-builder /root/.local /home/passeur/.local

# Copy Node.js dependencies and bridge code
COPY --from=node-builder /app/bridge ./bridge

# Copy configuration and source code
COPY --chown=passeur:passeur config/ ./config/
COPY --chown=passeur:passeur src/ ./src/

# Switch to non-root user
USER passeur

# Update PATH
ENV PATH=/home/passeur/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV NODE_ENV=production

# Expose bridge port
EXPOSE 8766

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8766/health || exit 1

# Run bridge server in production mode
CMD ["node", "bridge/server.js"]

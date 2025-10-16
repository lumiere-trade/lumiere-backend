# Multi-stage Dockerfile for Passeur (Python + Node.js)

FROM node:18-alpine as node-base

WORKDIR /app

# Install Node.js dependencies
COPY bridge/package*.json ./bridge/
RUN cd bridge && npm ci

# Copy bridge code
COPY bridge/ ./bridge/

FROM python:3.11-slim as python-builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

# Copy Python dependencies
COPY pyproject.toml ./
COPY src/ ./src/

# Install Python dependencies
RUN pip install --user --no-cache-dir .

# Final stage - combining both
FROM python:3.11-slim as production

# Install Node.js
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 passeur

WORKDIR /app

# Copy Python packages
COPY --from=python-builder /root/.local /home/passeur/.local

# Copy Node.js dependencies and code
COPY --from=node-base /app/bridge /app/bridge

# Copy Python code
COPY --chown=passeur:passeur src/ ./src/
COPY --chown=passeur:passeur config/ ./config/

# Switch to non-root user
USER passeur

# Update PATH
ENV PATH=/home/passeur/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV NODE_ENV=production

# Expose bridge port
EXPOSE 8766

# Run bridge server
CMD ["node", "bridge/server.js"]

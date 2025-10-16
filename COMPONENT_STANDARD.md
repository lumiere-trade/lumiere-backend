# Lumiere Component Standard

**Project-Wide Development Standard for All Components**

This document defines the mandatory structure, configuration, and deployment patterns for all Lumiere components. Every component must follow this standard for consistency, maintainability, and scalability.

**Reference Implementations:**
- **Pourtier** - Standard Python FastAPI component (typical case)
- **Passeur** - Hybrid Python + Node.js bridge (special case for blockchain interaction)

---

## Table of Contents

1. [Core Principles](#core-principles)
2. [Directory Structure](#directory-structure)
3. [Python Package Layout](#python-package-layout)
4. [Configuration Management](#configuration-management)
5. [Docker Implementation](#docker-implementation)
6. [Build System Makefile](#build-system-makefile)
7. [Systemd Service](#systemd-service)
8. [Security and Keypair Management](#security-and-keypair-management)
9. [Testing Structure](#testing-structure)
10. [Code Quality Standards](#code-quality-standards)
11. [Component Types](#component-types)
12. [Checklist](#checklist)

---

## Core Principles

### 1. Consistency
- All components follow identical structure
- Same build commands across all components
- Predictable file locations
- Master Makefile auto-discovers components

### 2. Security First
- No secrets in git repositories
- No secrets in Docker images  
- Keypairs stored centrally, mounted as read-only volumes
- Environment variables for all sensitive data

### 3. Scalability
- Easy to add new components
- Standard deployment process
- Docker-based deployment
- Systemd service management

### 4. Maintainability
- Clear separation of concerns (Clean Architecture / DDD)
- src layout for all Python code (mandatory)
- Comprehensive testing (unit, integration, e2e)
- Well-documented code

### 5. Code Quality
- PEP 8 compliance for Python
- Type hints for all functions
- Clear, concise comments in English
- Professional logging with appropriate levels

---

## Directory Structure

### Standard Python Component (Pourtier Pattern)

Most components are Python FastAPI services:
```
component_name/
├── config/
│   ├── component_name.yaml         # Production defaults (non-sensitive)
│   └── test.yaml                   # Test configuration
├── src/                            # MANDATORY: src layout
│   └── component_name/
│       ├── __init__.py
│       ├── main.py                 # Application entry point
│       ├── config/
│       │   ├── __init__.py
│       │   └── settings.py         # Pydantic Settings
│       ├── application/            # Application layer
│       │   ├── dto/
│       │   ├── use_cases/
│       │   └── subscribers/
│       ├── domain/                 # Domain layer
│       │   ├── entities/
│       │   ├── repositories/       # Interfaces
│       │   ├── services/
│       │   ├── value_objects/
│       │   ├── events/
│       │   └── exceptions/
│       ├── infrastructure/         # Infrastructure layer
│       │   ├── persistence/
│       │   │   ├── database.py
│       │   │   ├── models.py
│       │   │   └── repositories/   # Implementations
│       │   ├── blockchain/
│       │   ├── auth/
│       │   ├── event_bus/
│       │   └── external/
│       ├── presentation/           # Presentation layer
│       │   ├── api/
│       │   │   ├── routes/
│       │   │   └── middleware/
│       │   └── schemas/
│       └── di/                     # Dependency Injection
│           ├── container.py
│           └── dependencies.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── unit/
│   ├── integration/
│   ├── e2e/
│   ├── fixtures/
│   └── helpers/
├── scripts/                        # DB migrations, seed data
├── .env.example                    # IN GIT
├── .env.development                # NOT in git
├── .env.test                       # NOT in git
├── .env.production.example         # IN GIT
├── .gitignore
├── Dockerfile
├── Makefile
├── pyproject.toml
└── README.md
```

### Special Case: Hybrid Component (Passeur Pattern)

For components requiring Node.js blockchain interaction:
```
passeur/
├── bridge/                         # Node.js bridge server
│   ├── instructions/
│   │   ├── index.js
│   │   ├── initialize_escrow.js
│   │   └── discriminators.js
│   ├── package.json
│   └── server.js
├── config/
├── src/
│   └── passeur/
│       ├── cli/
│       ├── config/
│       └── utils/
├── tests/
├── Dockerfile                      # Multi-stage: Node + Python
├── Makefile
└── pyproject.toml
```

---

## Python Package Layout

### src Layout - Mandatory

**Every Python component MUST use src layout.**

WRONG (flat layout):
```
component_name/
├── component_name/         # WRONG
│   └── __init__.py
└── setup.py
```

CORRECT (src layout):
```
component_name/
├── src/                    # CORRECT
│   └── component_name/
│       └── __init__.py
└── pyproject.toml
```

**Why src layout:**
- Prevents accidental imports from project root
- Forces proper package installation
- Industry best practice (PEP 517/518)
- Better testing isolation
- Required for editable installs

### pyproject.toml Template
```toml
[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "component-name"
version = "0.1.0"
description = "Component description"
readme = "README.md"
requires-python = ">=3.11"
license = {text = "MIT"}

dependencies = [
    "shared",
    "fastapi>=0.104.0",
    "uvicorn[standard]>=0.24.0",
    "sqlalchemy>=2.0.0",
    "pydantic>=2.0.0",
    "pydantic-settings>=2.1.0",
    "pyyaml>=6.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.1.0",
    "black>=23.0.0",
    "isort>=5.12.0",
    "ruff>=0.1.6",
]

[project.scripts]
component-name = "component_name.main:main"

# CRITICAL: src layout configuration
[tool.setuptools]
package-dir = {"" = "src"}

[tool.setuptools.packages.find]
where = ["src"]
include = ["component_name*"]

[tool.black]
line-length = 88
target-version = ["py311"]

[tool.isort]
profile = "black"
line_length = 88

[tool.ruff]
line-length = 88
target-version = "py311"
```

---

## Configuration Management

### Hybrid YAML + ENV Pattern

**YAML files** - Non-sensitive defaults (in git)
**ENV files** - Sensitive data (NOT in git)

### Settings Implementation

**File: `src/component_name/config/settings.py`**
```python
"""
Component configuration with hybrid YAML + ENV support.

Priority: Environment variables > YAML config > Pydantic defaults
"""

import os
from pathlib import Path
from typing import Optional

import yaml
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Component configuration schema.
    
    Loading priority:
    1. Environment variables (highest)
    2. YAML configuration
    3. Pydantic defaults (lowest)
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow",
    )
    
    # Application
    APP_NAME: str = "Component"
    APP_VERSION: str = "0.1.0"
    ENV: str = Field(default="development")
    DEBUG: bool = Field(default=False)
    
    # API Server (from YAML or ENV)
    API_HOST: str = Field(default="0.0.0.0")
    API_PORT: int = Field(default=8000, ge=1024, le=65535)
    API_RELOAD: bool = Field(default=False)
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO")
    LOG_FILE: str = Field(default="logs/component.log")
    
    # Database (from ENV - sensitive)
    DATABASE_URL: str = Field(...)
    DATABASE_ECHO: bool = Field(default=False)
    
    # JWT (from ENV - sensitive)
    JWT_SECRET_KEY: str = Field(...)
    JWT_ALGORITHM: str = Field(default="HS256")
    JWT_EXPIRATION_HOURS: int = Field(default=24)
    
    # Blockchain (from ENV - if needed)
    SOLANA_RPC_URL: Optional[str] = Field(default=None)
    SOLANA_NETWORK: Optional[str] = Field(default=None)
    ESCROW_PROGRAM_ID: Optional[str] = Field(default=None)
    PLATFORM_KEYPAIR_PATH: Optional[str] = Field(default=None)
    
    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        allowed = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in allowed:
            raise ValueError(f"Invalid LOG_LEVEL: {v}")
        return v_upper
    
    @field_validator("PLATFORM_KEYPAIR_PATH")
    @classmethod
    def expand_keypair_path(cls, v: Optional[str]) -> Optional[str]:
        """Expand home directory in keypair path."""
        if v:
            return os.path.expanduser(v)
        return v


def load_config(config_file: Optional[str] = None) -> Settings:
    """
    Load configuration from YAML and environment.
    
    Args:
        config_file: YAML filename
    
    Returns:
        Settings instance
    """
    if config_file is None:
        env = os.getenv("ENV", "production")
        config_map = {
            "production": "component.yaml",
            "test": "test.yaml",
            "development": "component.yaml",
        }
        config_file = config_map.get(env, "component.yaml")
    
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent.parent
    config_path = project_root / "config" / config_file
    
    yaml_config = {}
    if config_path.exists():
        with open(config_path, "r") as f:
            loaded = yaml.safe_load(f)
            if loaded:
                yaml_config = loaded
    
    return Settings(**yaml_config)


settings: Settings = load_config()
```

### YAML Configuration Files

**File: `config/component_name.yaml`**
```yaml
# Component Production Configuration
# Non-sensitive defaults only

# API Server
API_HOST: "0.0.0.0"
API_PORT: 8000
API_RELOAD: false

# Logging
LOG_LEVEL: "INFO"
LOG_FILE: "logs/component.log"

# Database
DATABASE_ECHO: false

# Redis
REDIS_ENABLED: true
REDIS_HOST: "localhost"
REDIS_PORT: 6379
```

**File: `config/test.yaml`**
```yaml
# Component Test Configuration

# API Server (different port)
API_HOST: "127.0.0.1"
API_PORT: 8001
API_RELOAD: true

# Logging (verbose)
LOG_LEVEL: "DEBUG"
LOG_FILE: "tests/logs/component.log"

# Database
DATABASE_ECHO: true
```

### Environment Files

**File: `.env.development`** (NOT in git)
```bash
# Development Environment

ENV=development
DEBUG=true

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/component_dev

# JWT
JWT_SECRET_KEY=dev-secret-change-in-production

# Blockchain (if needed)
SOLANA_RPC_URL=https://api.devnet.solana.com
SOLANA_NETWORK=devnet
ESCROW_PROGRAM_ID=9gvUtaF99sQ287PNzRfCbhFTC4PUnnd7jdAjnY5GUVhS
PLATFORM_KEYPAIR_PATH=/root/lumiere/keypairs/dev/platform.json

# External Services
PASSEUR_BRIDGE_URL=http://localhost:8766
COURIER_URL=http://localhost:8765
```

**File: `.env.production`** (NOT in git)
```bash
# Production Environment

ENV=production
DEBUG=false

# Database
DATABASE_URL=postgresql+asyncpg://user:SECURE_PASSWORD@localhost:5432/component_prod

# JWT
JWT_SECRET_KEY=GENERATE_STRONG_SECRET_KEY_HERE

# Blockchain
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
SOLANA_NETWORK=mainnet-beta
ESCROW_PROGRAM_ID=YOUR_PRODUCTION_PROGRAM_ID
PLATFORM_KEYPAIR_PATH=/root/lumiere/keypairs/prod/platform.json

# External Services  
PASSEUR_BRIDGE_URL=http://localhost:8766
COURIER_URL=http://localhost:8765
```

### .gitignore
```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv*/
*.egg-info/
dist/
build/

# Environment files (NEVER commit)
.env
.env.local
.env.development
.env.test
.env.production

# Logs
logs/
*.log

# IDE
.vscode/
.idea/
*.swp

# OS
.DS_Store
Thumbs.db
```

---

## Docker Implementation

### Multi-Stage Dockerfile

Every component must have a multi-stage Dockerfile with **development** and **production** targets.

**File: `Dockerfile` (Standard Python Component)**
```dockerfile
# ============================================
# Multi-stage Dockerfile for Python Component
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
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy package files
COPY pyproject.toml ./
COPY src/ ./src/

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --user --no-cache-dir .

# ============================================
# Stage 2: Development
# ============================================
FROM python:3.11-slim AS development

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages
COPY --from=python-builder /root/.local /root/.local

# Update PATH
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Copy application code
COPY . .

# Install in editable mode for development
RUN pip install --no-cache-dir -e ".[dev]"

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run with auto-reload
CMD ["uvicorn", "component_name.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--reload", \
     "--log-level", "info"]

# ============================================
# Stage 3: Production
# ============================================
FROM python:3.11-slim AS production

# Create non-root user
RUN useradd -m -u 1000 -s /bin/bash component_user && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy Python packages
COPY --from=python-builder /root/.local /home/component_user/.local

# Copy application code
COPY --chown=component_user:component_user . .

# Switch to non-root user
USER component_user

# Update PATH
ENV PATH=/home/component_user/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run production server
CMD ["uvicorn", "component_name.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "4", \
     "--loop", "uvloop"]
```

### Docker Image Naming Standard
```
component_name:development  # Development image
component_name:production   # Production image
component_name:latest       # Alias for production
```

**NEVER use:**
- component:dev (ambiguous)
- component:prod (ambiguous)  
- component:test (test is not an environment)

---

## Build System Makefile

### Component Makefile

Every component must have its own Makefile.

**File: `Makefile`**
```makefile
# Component Makefile
# Standard build commands

.PHONY: help build-dev build-prod run-dev run-prod clean

COMPONENT = component_name
PORT = 8000
KEYPAIRS_DIR = $(HOME)/lumiere/keypairs

help:
	@echo "=== $(COMPONENT) Docker Commands ==="
	@echo "make build-dev   - Build development image"
	@echo "make build-prod  - Build production image"
	@echo "make run-dev     - Run development container"
	@echo "make run-prod    - Run production container"
	@echo "make clean       - Remove images"

build-dev:
	@echo "[BUILD] Building $(COMPONENT):development..."
	docker build --target development -t $(COMPONENT):development .
	@echo "[SUCCESS] Built $(COMPONENT):development"

build-prod:
	@echo "[BUILD] Building $(COMPONENT):production..."
	docker build --target production -t $(COMPONENT):production .
	docker tag $(COMPONENT):production $(COMPONENT):latest
	@echo "[SUCCESS] Built $(COMPONENT):production"

run-dev:
	@echo "[RUN] Starting $(COMPONENT):development on port $(PORT)..."
	docker run --rm -p $(PORT):$(PORT) \
		--env-file .env.development \
		-v $(KEYPAIRS_DIR)/dev:/root/lumiere/keypairs/dev:ro \
		--name $(COMPONENT)-dev \
		$(COMPONENT):development

run-prod:
	@echo "[RUN] Starting $(COMPONENT):production on port $(PORT)..."
	docker run --rm -p $(PORT):$(PORT) \
		--env-file .env.production \
		-v $(KEYPAIRS_DIR)/prod:/root/lumiere/keypairs/prod:ro \
		--name $(COMPONENT)-prod \
		$(COMPONENT):production

clean:
	@echo "[CLEAN] Removing $(COMPONENT) images..."
	docker rmi $(COMPONENT):development $(COMPONENT):production $(COMPONENT):latest 2>/dev/null || true
	@echo "[SUCCESS] Cleaned"
```

### Master Makefile (Project Root)

**File: `~/lumiere/lumiere-public/Makefile`**
```makefile
# Lumiere Project - Master Makefile
# Auto-discovers all components

.PHONY: help list-components

# Find components
COMPONENTS := $(dir $(wildcard */Makefile))
COMPONENTS := $(COMPONENTS:/=)

# Colors
GREEN = \033[0;32m
YELLOW = \033[0;33m
BLUE = \033[0;34m
NC = \033[0m

help:
	@echo "=================================="
	@echo "Lumiere Docker Management"
	@echo "=================================="
	@echo ""
	@echo "Usage: make <component>-<action>"
	@echo ""
	@echo "Actions:"
	@echo "  build-dev    - Build development image"
	@echo "  build-prod   - Build production image"
	@echo "  run-dev      - Run development container"
	@echo "  run-prod     - Run production container"
	@echo "  clean        - Remove images"
	@echo ""
	@echo "Examples:"
	@echo "  make passeur-build-dev"
	@echo "  make pourtier-build-prod"
	@echo ""
	@echo "Bulk actions:"
	@echo "  make build-all-dev"
	@echo "  make build-all-prod"
	@echo "  make clean-all"
	@echo ""
	@echo "Other:"
	@echo "  make list-components"

list-components:
	@echo "$(BLUE)[INFO]$(NC) Discovered components:"
	@for comp in $(COMPONENTS); do \
		echo "  - $$comp"; \
	done

# Generic rules
%-build-dev:
	@component=$*; \
	if [ -d "$$component" ] && [ -f "$$component/Makefile" ]; then \
		echo "$(GREEN)[$$component]$(NC) Building development..."; \
		cd $$component && $(MAKE) build-dev; \
	else \
		echo "$(YELLOW)[ERROR]$(NC) Component not found"; \
		exit 1; \
	fi

%-build-prod:
	@component=$*; \
	if [ -d "$$component" ] && [ -f "$$component/Makefile" ]; then \
		echo "$(GREEN)[$$component]$(NC) Building production..."; \
		cd $$component && $(MAKE) build-prod; \
	else \
		echo "$(YELLOW)[ERROR]$(NC) Component not found"; \
		exit 1; \
	fi

%-run-dev:
	@component=$*; \
	if [ -d "$$component" ] && [ -f "$$component/Makefile" ]; then \
		echo "$(GREEN)[$$component]$(NC) Running development..."; \
		cd $$component && $(MAKE) run-dev; \
	else \
		echo "$(YELLOW)[ERROR]$(NC) Component not found"; \
		exit 1; \
	fi

%-run-prod:
	@component=$*; \
	if [ -d "$$component" ] && [ -f "$$component/Makefile" ]; then \
		echo "$(GREEN)[$$component]$(NC) Running production..."; \
		cd $$component && $(MAKE) run-prod; \
	else \
		echo "$(YELLOW)[ERROR]$(NC) Component not found"; \
		exit 1; \
	fi

%-clean:
	@component=$*; \
	if [ -d "$$component" ] && [ -f "$$component/Makefile" ]; then \
		echo "$(YELLOW)[$$component]$(NC) Cleaning..."; \
		cd $$component && $(MAKE) clean; \
	else \
		echo "$(YELLOW)[ERROR]$(NC) Component not found"; \
		exit 1; \
	fi

# Bulk commands
build-all-dev:
	@for comp in $(COMPONENTS); do \
		echo "$(GREEN)[$$comp]$(NC) Building development..."; \
		cd $$comp && $(MAKE) build-dev || exit 1; \
		cd ..; \
	done
	@echo "$(GREEN)[SUCCESS]$(NC) All development images built"

build-all-prod:
	@for comp in $(COMPONENTS); do \
		echo "$(GREEN)[$$comp]$(NC) Building production..."; \
		cd $$comp && $(MAKE) build-prod || exit 1; \
		cd ..; \
	done
	@echo "$(GREEN)[SUCCESS]$(NC) All production images built"

clean-all:
	@for comp in $(COMPONENTS); do \
		echo "$(YELLOW)[$$comp]$(NC) Cleaning..."; \
		cd $$comp && $(MAKE) clean || true; \
		cd ..; \
	done
	@echo "$(GREEN)[SUCCESS]$(NC) All images cleaned"
```

**Usage:**
```bash
# From project root
make passeur-build-dev      # Build passeur development
make pourtier-build-prod    # Build pourtier production
make build-all-dev          # Build all development images
make list-components        # Show all components

# From component directory
cd passeur
make build-dev              # Build development
make run-dev                # Run development
```

---

## Systemd Service

Every production component must have a systemd service.

**File: `/etc/systemd/system/component_name.service`**
```ini
[Unit]
Description=Component Name Service (Docker)
After=docker.service
Requires=docker.service

[Service]
Type=simple
User=root
WorkingDirectory=/root/lumiere/lumiere-public/component_name

# Stop old container
ExecStartPre=-/usr/bin/docker stop component-production
ExecStartPre=-/usr/bin/docker rm component-production

# Start production container
ExecStart=/usr/bin/docker run --rm \
    --name component-production \
    -p 8000:8000 \
    --env-file /root/lumiere/lumiere-public/component_name/.env.production \
    -v /root/lumiere/keypairs/prod:/root/lumiere/keypairs/prod:ro \
    component_name:production

# Stop gracefully
ExecStop=/usr/bin/docker stop component-production

# Restart policy
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Service Management:**
```bash
# Install service
sudo cp component_name.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable component_name.service

# Start service
sudo systemctl start component_name.service

# Check status
sudo systemctl status component_name.service

# View logs
sudo journalctl -u component_name.service -f

# Restart
sudo systemctl restart component_name.service

# Stop
sudo systemctl stop component_name.service
```

---

## Security and Keypair Management

### Centralized Keypair Storage

All keypairs stored outside project repository:
```
~/lumiere/keypairs/
├── dev/                    # Development (devnet)
│   ├── platform.json
│   ├── authority.json
│   └── test_users.json
└── prod/                   # Production (mainnet)
    ├── platform.json
    ├── authority.json
    └── treasury.json
```

### Test Fixtures (In Repository)

Mock keypairs for automated testing:
```
shared/blockchain/keypairs/
├── test/                   # Unit test mocks
└── production/             # Integration test mocks
```

### Keypair Security Rules
```bash
# Set secure permissions
chmod 600 ~/lumiere/keypairs/dev/*
chmod 600 ~/lumiere/keypairs/prod/*
chmod 700 ~/lumiere/keypairs/dev
chmod 700 ~/lumiere/keypairs/prod
```

### Docker Volume Mounting

Keypairs mounted as read-only volumes:
```bash
# Development
-v /root/lumiere/keypairs/dev:/root/lumiere/keypairs/dev:ro

# Production
-v /root/lumiere/keypairs/prod:/root/lumiere/keypairs/prod:ro
```

**Security Rules:**
- NEVER copy keypairs into Docker images
- NEVER commit keypairs to git
- NEVER store keypairs in environment variables
- ALWAYS mount as read-only (:ro)
- ALWAYS use secure permissions (600/700)

---

## Testing Structure

### Test Organization
```
tests/
├── __init__.py
├── conftest.py             # Pytest fixtures
├── unit/                   # Unit tests (no external dependencies)
│   ├── application/
│   └── domain/
├── integration/            # Integration tests (external services)
│   ├── api/
│   ├── database/
│   └── services/
├── e2e/                    # End-to-end tests
├── fixtures/               # Test data
└── helpers/                # Test utilities
```

### Test Base Class

Use shared.tests.LaborantTest for all tests:
```python
"""
Unit tests for Component.

Usage:
    python -m component.tests.unit.test_config
    laborant component --unit
"""

from shared.tests import LaborantTest
from component.config.settings import load_config


class TestComponentConfig(LaborantTest):
    """Unit tests for configuration."""
    
    component_name = "component"
    test_category = "unit"
    
    def setup(self):
        """Setup before tests."""
        self.config = load_config("test.yaml")
        self.reporter.info("Loaded test config", context="Setup")
    
    def test_default_values(self):
        """Test default configuration values."""
        self.reporter.info("Testing defaults", context="Test")
        
        assert self.config.API_PORT == 8000
        assert self.config.LOG_LEVEL == "INFO"
        
        self.reporter.info("Defaults correct", context="Test")
```

### Running Tests
```bash
# All tests
pytest component/tests/

# Specific category
pytest component/tests/unit/
pytest component/tests/integration/

# With coverage
pytest component/tests/ --cov=component --cov-report=html

# Using laborant
laborant component --unit
laborant component --integration
```

---

## Code Quality Standards

### Python Standards

1. **PEP 8 Compliance**
   - Line length: 88 characters (Black default)
   - Use Black for formatting
   - Use isort for imports

2. **Type Hints**
   - All functions must have type hints
   - Use Optional[T] for nullable types
   - Use typing module types

3. **Documentation**
   - All modules, classes, functions must have docstrings
   - Use Google-style docstrings
   - Clear parameter and return descriptions

4. **Comments**
   - Clear, concise English comments
   - Explain WHY, not WHAT
   - No commented-out code in production

5. **Logging**
   - Use appropriate log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
   - Include context in log messages
   - Use structured logging where possible

### Example Function Documentation
```python
def create_user(
    wallet_address: str,
    email: Optional[str] = None
) -> User:
    """
    Create a new user account.
    
    Args:
        wallet_address: Solana wallet address (base58 string)
        email: Optional email address for notifications
    
    Returns:
        Created User entity
    
    Raises:
        ValueError: If wallet_address format is invalid
        UserAlreadyExistsError: If user with wallet already exists
    
    Example:
        >>> user = create_user("7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU")
        >>> print(user.wallet_address)
        7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU
    """
    # Validate wallet address format
    if not is_valid_solana_address(wallet_address):
        raise ValueError(f"Invalid wallet address: {wallet_address}")
    
    # Check if user already exists
    existing_user = user_repository.get_by_wallet(wallet_address)
    if existing_user:
        raise UserAlreadyExistsError(wallet_address)
    
    # Create new user
    user = User(wallet_address=wallet_address, email=email)
    user_repository.save(user)
    
    logger.info(
        "Created new user",
        extra={"wallet": wallet_address, "has_email": email is not None}
    )
    
    return user
```

---

## Component Types

### Type 1: Standard Python FastAPI Component

**Example: Pourtier**

Characteristics:
- Python FastAPI web service
- PostgreSQL database
- Clean Architecture / DDD layers
- REST API endpoints
- JWT authentication
- No Node.js bridge

Components: Most components (Pourtier, Chevalier API, etc.)

### Type 2: Hybrid Python + Node.js Component

**Example: Passeur**

Characteristics:
- Python CLI/utilities
- Node.js Express + WebSocket server
- Direct Solana blockchain interaction
- Multi-stage Dockerfile (Node + Python)
- Bridge pattern for blockchain calls

Components: Passeur (only blockchain bridge)

### Type 3: Background Worker Component

Characteristics:
- No web server
- Background processing
- Event-driven
- Cron jobs or continuous loop

Components: Feeder, Rebalancer (future)

---

## Checklist

### New Component Checklist

When creating a new component, verify:

**Structure:**
- [ ] Uses src layout (not flat layout)
- [ ] Has config/ directory with YAML files
- [ ] Has tests/ with unit/integration/e2e
- [ ] Has proper .gitignore

**Configuration:**
- [ ] pyproject.toml with correct package-dir
- [ ] settings.py with Pydantic Settings
- [ ] .env.example in git
- [ ] .env.development NOT in git
- [ ] .env.production.example in git

**Docker:**
- [ ] Multi-stage Dockerfile
- [ ] development target
- [ ] production target
- [ ] Health check implemented
- [ ] Non-root user in production

**Build System:**
- [ ] Component Makefile exists
- [ ] Standard targets (build-dev, build-prod, run-dev, run-prod, clean)
- [ ] Correct COMPONENT and PORT variables
- [ ] Keypairs mounted as read-only

**Production:**
- [ ] .env.production created (not in git)
- [ ] Production Docker image built
- [ ] Systemd service file created
- [ ] Service enabled and tested

**Code Quality:**
- [ ] PEP 8 compliant
- [ ] Type hints on all functions
- [ ] Docstrings on all modules/classes/functions
- [ ] Tests cover critical paths
- [ ] No secrets in code

**Documentation:**
- [ ] README.md with overview, setup, usage
- [ ] API documentation (if web service)
- [ ] Configuration documentation
- [ ] Deployment instructions

### Migration Checklist

When migrating existing component to this standard:

- [ ] Convert to src layout
- [ ] Update pyproject.toml
- [ ] Create hybrid settings.py
- [ ] Split config into YAML + ENV
- [ ] Create multi-stage Dockerfile
- [ ] Create component Makefile
- [ ] Test Docker builds
- [ ] Create systemd service
- [ ] Update documentation
- [ ] Verify in master Makefile

---

## Summary

This standard ensures:
- Consistency across all components
- Easy onboarding for new developers
- Secure handling of sensitive data
- Reproducible builds and deployments
- Scalable architecture

**When in doubt, refer to Pourtier as the reference implementation for standard components.**


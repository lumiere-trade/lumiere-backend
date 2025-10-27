# Pourtier Development Guide

**Version:** 1.0  
**Date:** October 27, 2025  
**For:** Developers setting up local environment

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Setup](#local-setup)
3. [Configuration](#configuration)
4. [Running the Service](#running-the-service)
5. [Testing](#testing)
6. [Code Standards](#code-standards)
7. [Git Workflow](#git-workflow)
8. [Build & Deployment](#build--deployment)
9. [Debugging](#debugging)
10. [Service Discovery](#service-discovery)

---

## Prerequisites

### Required

**System:**
- Ubuntu 22.04+ or Debian 11+
- Python 3.11+
- PostgreSQL 16
- Redis 7+
- Docker 24+ & Docker Compose 2+
- Git 2.40+

**Docker BuildX:**
- Docker BuildX plugin
- lumiere-builder buildx instance (multi-platform support)

### Optional

- pyenv (Python version management)
- pgAdmin 4 (database GUI)
- Postman or HTTPie (API testing)
- VSCode with Python extension

---

### Installation Commands

**Ubuntu/Debian:**
```bash
# System update
sudo apt update && sudo apt upgrade -y

# Python 3.11
sudo apt install python3.11 python3.11-venv python3.11-dev -y

# PostgreSQL 16
sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
sudo apt update
sudo apt install postgresql-16 -y

# Redis
sudo apt install redis-server -y

# Docker & Docker Compose
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Docker BuildX
docker buildx create --name lumiere-builder --driver docker-container --bootstrap
docker buildx use lumiere-builder
docker buildx inspect
```

**Verify installations:**
```bash
python3.11 --version  # Should be 3.11.x
psql --version        # Should be 16.x
redis-cli --version   # Should be 7.x
docker --version      # Should be 24.x+
docker buildx version # Should show buildx
```

---

## Local Setup

### 1. Clone Repository
```bash
cd ~
git clone https://github.com/lumiere-trade/lumiere-backend.git
cd lumiere-backend/pourtier
```

### 2. Create Virtual Environment
```bash
# Create venv
python3.11 -m venv venv311

# Activate venv
source venv311/bin/activate  # Linux/macOS
# or
venv311\Scripts\activate  # Windows

# Upgrade pip
pip install --upgrade pip setuptools wheel
```

### 3. Install Dependencies

**Option A: Editable install (recommended for development)**
```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Verify installation
python -c "import pourtier; print(pourtier.__version__)"
```

**Option B: Regular install**
```bash
pip install .
```

**Install shared package:**
```bash
# If using private PyPI registry
pip install shared --index-url http://localhost:9001/simple/ --trusted-host localhost

# Or install from local source
cd ../shared
pip install -e .
cd ../pourtier
```

### 4. Setup Database

**Create database:**
```bash
# Switch to postgres user
sudo -u postgres psql

# Create database and user
CREATE DATABASE lumiere_pourtier;
CREATE USER lumiere_dev WITH PASSWORD 'your_dev_password';
GRANT ALL PRIVILEGES ON DATABASE lumiere_pourtier TO lumiere_dev;
\q
```

**Run migrations:**
```bash
# Install Alembic if not included
pip install alembic

# Run migrations
alembic upgrade head

# Verify
psql -U lumiere_dev -d lumiere_pourtier -c "\dt"
```

**Seed test data (optional):**
```bash
python scripts/seed_data.py
```

### 5. Setup Configuration

**Copy example configs:**
```bash
# Copy environment example
cp .env.example .env.development

# Copy production example
cp .env.production.example .env.production

# Edit development config
nano .env.development
```

**Minimal .env.development:**
```bash
# Environment
ENV=development

# Database
DATABASE_URL=postgresql://lumiere_dev:your_dev_password@localhost:5432/lumiere_pourtier

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT (generate secret: openssl rand -hex 32)
JWT_SECRET_KEY=your_jwt_secret_key_here

# Solana (Devnet for development)
SOLANA_RPC_URL=https://api.devnet.solana.com
SOLANA_NETWORK=devnet

# Service URLs (Docker DNS names)
COURIER_URL=http://courier:9765
PASSEUR_URL=http://passeur:9766
```

**Edit YAML configs:**
```bash
# Edit development.yaml
nano config/development.yaml
```

### 6. Verify Setup

**Health check script:**
```bash
# Create quick health check
cat > check_setup.sh << 'SCRIPT'
#!/bin/bash
echo "=== Pourtier Setup Check ==="

# Python version
echo -n "Python: "
python --version

# Database connection
echo -n "PostgreSQL: "
psql $DATABASE_URL -c "SELECT 1" > /dev/null 2>&1 && echo "OK" || echo "FAILED"

# Redis connection
echo -n "Redis: "
redis-cli ping > /dev/null 2>&1 && echo "OK" || echo "FAILED"

# Config loading
echo -n "Config: "
python -c "from pourtier.config.settings import get_settings; get_settings()" > /dev/null 2>&1 && echo "OK" || echo "FAILED"

echo "=== Setup Complete ==="
SCRIPT

chmod +x check_setup.sh
./check_setup.sh
```

---

## Configuration

### Configuration Priority

**Loading Order (highest to lowest):**
1. Environment variables (CLI or .env file)
2. YAML config file (development.yaml/production.yaml)
3. Pydantic default values

### Environment Variables

**Required:**
```bash
DATABASE_URL="postgresql://user:pass@localhost:5432/lumiere_pourtier"
JWT_SECRET_KEY="your-secret-key"
REDIS_URL="redis://localhost:6379/0"
```

**Optional:**
```bash
ENV="development"              # development | production | test
LOG_LEVEL="INFO"               # DEBUG | INFO | WARNING | ERROR
API_HOST="0.0.0.0"            # Bind address
API_PORT="9000"               # API port
DEBUG="true"                  # Enable debug mode
```

### YAML Configuration Files

**config/development.yaml:**
```yaml
# API Server
API_HOST: "0.0.0.0"
API_PORT: 9000
API_RELOAD: true               # Hot reload in development

# Logging
LOG_LEVEL: "DEBUG"
LOG_FILE: "logs/pourtier-dev.log"

# Database
DATABASE_ECHO: true            # Log SQL queries

# Service URLs (Docker DNS)
courier_url: "http://courier:9765"
passeur_url: "http://passeur:9766"

# Cache
CACHE_TTL_USER: 300           # 5 minutes
CACHE_TTL_SUBSCRIPTION: 60    # 1 minute

# Security
JWT_EXPIRE_MINUTES: 30
CORS_ORIGINS:
  - "http://localhost:3000"
  - "http://localhost:3001"
```

**config/production.yaml:**
```yaml
# API Server
API_HOST: "0.0.0.0"
API_PORT: 8000
API_RELOAD: false

# Logging
LOG_LEVEL: "INFO"
LOG_FILE: null                 # Stdout for Docker logs

# Database
DATABASE_ECHO: false           # No SQL logging in production

# Service URLs (Docker DNS)
courier_url: "http://courier:8765"
passeur_url: "http://passeur:8766"

# Cache
CACHE_TTL_USER: 300
CACHE_TTL_SUBSCRIPTION: 60

# Security
JWT_EXPIRE_MINUTES: 30
CORS_ORIGINS:
  - "https://app.lumiere.trade"
```

---

## Running the Service

### Development Mode (Local)

**Without Docker:**
```bash
# Activate venv
source venv311/bin/activate

# Start service with hot reload
uvicorn pourtier.main:app --reload --port 9000 --host 0.0.0.0

# Or use the CLI
python -m pourtier
```

**Check health:**
```bash
curl http://localhost:9000/health
# Expected: {"status": "healthy", "version": "0.1.0"}
```

---

### Development Mode (Docker Compose)

**Start all services:**
```bash
cd ~/lumiere/lumiere-backend

# Start development stack
docker compose -f docker-compose.development.yaml up -d

# View logs
docker compose -f docker-compose.development.yaml logs -f pourtier

# Check status
docker compose -f docker-compose.development.yaml ps
```

**Access services:**
- Pourtier API: http://localhost:9000
- API Docs: http://localhost:9000/docs
- Courier: http://localhost:9765
- Passeur: http://localhost:9766

**Stop services:**
```bash
# Stop all services
docker compose -f docker-compose.development.yaml down

# Stop and remove volumes (WARNING: deletes data!)
docker compose -f docker-compose.development.yaml down -v
```

---

### Production Mode

**Using systemd:**
```bash
# Start service
sudo systemctl start lumiere-dev

# Check status
sudo systemctl status lumiere-dev

# View logs
sudo journalctl -u lumiere-dev -f

# Stop service
sudo systemctl stop lumiere-dev
```

**Using Docker directly:**
```bash
# Build production image
cd ~/lumiere/lumiere-backend
docker buildx build -f pourtier/Dockerfile --target production -t pourtier:production --load .

# Run production container
docker run -d \
  --name pourtier-prod \
  -p 8000:8000 \
  -v /root/lumiere/keypairs/prod:/root/lumiere/keypairs/prod:ro \
  --env-file pourtier/.env.production \
  pourtier:production

# Check logs
docker logs pourtier-prod -f
```

---

### Service Discovery (Docker DNS)

When running in Docker, services communicate using **Docker DNS names**:
```python
# In config/development.yaml
courier_url: "http://courier:9765"   # Not localhost!
passeur_url: "http://passeur:9766"

# Docker resolves 'courier' → container IP automatically
```

**Test DNS resolution:**
```bash
# From inside Pourtier container
docker exec lumiere-pourtier getent hosts courier
# Output: 172.18.0.3      courier

# Test HTTP communication
docker exec lumiere-pourtier curl -s http://courier:9765/health
```

**See full documentation:** [SERVICE_DISCOVERY.md](/mnt/project/SERVICE_DISCOVERY.md)

---

## Testing

### Running Tests

**All tests:**
```bash
# Using pytest directly
pytest

# Using Laborant
laborant test pourtier
```

**Specific test types:**
```bash
# Unit tests only (no external dependencies)
pytest tests/unit/
laborant test pourtier --unit

# Integration tests (requires services)
pytest tests/integration/
laborant test pourtier --integration

# E2E tests (full stack)
pytest tests/e2e/
laborant test pourtier --e2e

# Specific test file
pytest tests/unit/test_user_service.py

# Specific test function
pytest tests/unit/test_user_service.py::test_create_user
```

**With coverage:**
```bash
# Generate coverage report
pytest --cov=pourtier --cov-report=html

# Open coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

**With verbose output:**
```bash
pytest -v -s
```

---

### Test Database

Tests use a separate database:

**Setup test database:**
```bash
# Create test database
sudo -u postgres psql -c "CREATE DATABASE lumiere_pourtier_test;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE lumiere_pourtier_test TO lumiere_dev;"

# Run migrations
DATABASE_URL="postgresql://lumiere_dev:your_dev_password@localhost:5432/lumiere_pourtier_test" alembic upgrade head
```

**Test configuration (.env.test):**
```bash
ENV=test
DATABASE_URL=postgresql://lumiere_dev:your_dev_password@localhost:5432/lumiere_pourtier_test
REDIS_URL=redis://localhost:6379/1  # Different Redis DB
JWT_SECRET_KEY=test_secret_key
```

---

### Docker Test Environment

**Run tests in Docker:**
```bash
cd ~/lumiere/lumiere-backend

# Start test stack
docker compose -f docker-compose.test.yaml --profile integration up -d

# Run integration tests
laborant test pourtier --integration

# Cleanup
docker compose -f docker-compose.test.yaml down -v
```

**Test ports (7xxx range):**
- Pourtier: 7000
- Courier: 7765
- Passeur: 7766
- PostgreSQL: 5433 (exposed for external access)

---

### Writing Tests

**Unit test example:**
```python
# tests/unit/application/test_create_user.py

import pytest
from uuid import UUID
from pourtier.application.use_cases.create_user import CreateUser
from pourtier.domain.entities.user import User

@pytest.fixture
def mock_user_repository():
    """Mock user repository."""
    return MockUserRepository()

@pytest.mark.asyncio
async def test_create_user_success(mock_user_repository):
    """Test successful user creation."""
    # Arrange
    use_case = CreateUser(user_repository=mock_user_repository)
    wallet_address = "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU"
    
    # Act
    user = await use_case.execute(wallet_address=wallet_address)
    
    # Assert
    assert isinstance(user, User)
    assert user.wallet_address == wallet_address
    assert isinstance(user.id, UUID)
    assert user.escrow_account is None  # Not initialized yet
```

**Integration test example:**
```python
# tests/integration/api/test_auth_routes.py

import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_verify_wallet_endpoint(client: AsyncClient):
    """Test wallet verification endpoint."""
    # Arrange
    wallet_address = "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU"
    
    # Act
    response = await client.post("/api/auth/verify", json={
        "wallet_address": wallet_address,
        "wallet_type": "Phantom"
    })
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "nonce" in data
    assert "message" in data
    assert wallet_address in data["message"]
```

---

## Code Standards

### Python Style Guide

**PEP 8 Compliance:**
- Line length: **88 characters** (Black default)
- Indentation: 4 spaces (no tabs)
- Imports: Organized (stdlib → third-party → local)

**Type Hints (MANDATORY):**
```python
# All functions must have type hints
from typing import Optional
from uuid import UUID

def create_user(
    wallet_address: str,
    email: Optional[str] = None
) -> User:
    ...

async def get_user_by_id(user_id: UUID) -> Optional[User]:
    ...
```

**Docstrings (Google style):**
```python
def calculate_subscription_fee(plan: str, months: int) -> Decimal:
    """
    Calculate subscription fee for given plan and duration.
    
    Args:
        plan: Subscription plan type ("basic" or "pro")
        months: Number of months to subscribe
        
    Returns:
        Total fee in USDC
        
    Raises:
        ValueError: If plan is invalid or months < 1
        
    Example:
        >>> calculate_subscription_fee("basic", 3)
        Decimal('87.00')
    """
    ...
```

---

### Code Formatting

**Automated formatters:**
```bash
# Format code with Black
black src/

# Sort imports with isort
isort src/

# Remove unused imports with autoflake
autoflake --remove-all-unused-imports --in-place --recursive src/

# Check style with flake8
flake8 src/
```

**Pre-commit hook (recommended):**
```bash
# Install pre-commit
pip install pre-commit

# Setup hook
pre-commit install

# Now formatters run automatically on git commit
```

**pyproject.toml configuration:**
```toml
[tool.black]
line-length = 88
target-version = ["py311"]

[tool.isort]
profile = "black"
line_length = 88

[tool.flake8]
max-line-length = 88
exclude = .git,__pycache__,venv*,build,dist
```

---

### No Technical Debt Policy

**Prohibited:**
- ❌ TODO comments without GitHub issue link
- ❌ Commented-out code
- ❌ `print()` statements (use logging)
- ❌ Hardcoded values (use configuration)
- ❌ `any` type hints (use specific types)
- ❌ Emojis in code (professional code only)

**Required:**
- ✅ All public functions have docstrings
- ✅ All functions have type hints
- ✅ Tests for new features
- ✅ Update docs when changing API
- ✅ Clean git history (squash before merge)

---

## Git Workflow

### Branch Naming
```
feature/short-description
bugfix/short-description
hotfix/short-description
docs/short-description
refactor/short-description
```

### Commit Messages

**Format:**
```
type(scope): subject

body (optional)

footer (optional)
```

**Types:**
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation changes
- `refactor` - Code refactoring
- `test` - Adding tests
- `chore` - Maintenance tasks
- `perf` - Performance improvements

**Examples:**
```bash
feat(auth): add wallet signature verification

Implement ed25519 signature verification for Solana wallets using
solders library. Validates message signature against wallet public key.

Closes #123

---

fix(escrow): handle insufficient balance error correctly

Return 400 Bad Request instead of 500 when user has insufficient
escrow balance for withdrawal.

---

docs(api): update authentication flow diagram

Add detailed sequence diagram for wallet-based authentication flow
including nonce generation and signature verification.
```

---

### Pull Request Process

1. **Create feature branch:**
```bash
git checkout -b feature/add-wallet-balance-endpoint
```

2. **Make changes with clean commits:**
```bash
git add src/pourtier/application/use_cases/get_wallet_balance.py
git commit -m "feat(wallet): add get wallet balance use case"
```

3. **Run tests:**
```bash
pytest
black src/
isort src/
flake8 src/
```

4. **Push branch:**
```bash
git push origin feature/add-wallet-balance-endpoint
```

5. **Create PR with description:**
   - Clear title describing change
   - Link to related issue
   - Description of what changed and why
   - Screenshots if UI changes

6. **Wait for CI and review:**
   - CI tests must pass
   - At least 1 approval required
   - Address review comments

7. **Squash merge to main:**
```bash
# Squash commits into one clean commit
git rebase -i main
git push -f
```

---

## Build & Deployment

### Docker Build

**Development image:**
```bash
cd ~/lumiere/lumiere-backend

# Build with Docker BuildX
docker buildx build \
  -f pourtier/Dockerfile \
  --target development \
  -t pourtier:development \
  --load \
  .

# Verify image
docker images | grep pourtier
```

**Production image:**
```bash
# Build production image
docker buildx build \
  -f pourtier/Dockerfile \
  --target production \
  -t pourtier:production \
  --load \
  .
```

**Using Makefile:**
```bash
cd ~/lumiere/lumiere-backend/pourtier

# Build development image
make build-dev

# Build production image
make build-prod

# Run development container
make run-dev

# Stop and cleanup
make clean
```

---

### Local Deployment (systemd)

**Setup systemd service:**
```bash
# Copy service file
sudo cp deployment/lumiere-dev.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable auto-start
sudo systemctl enable lumiere-dev

# Start service
sudo systemctl start lumiere-dev

# Check status
sudo systemctl status lumiere-dev

# View logs
sudo journalctl -u lumiere-dev -f
```

**Service file location:**
```
/etc/systemd/system/lumiere-dev.service
```

---

### Production Deployment

**Steps:**

1. **Run tests:**
```bash
pytest
```

2. **Build production image:**
```bash
make build-prod
```

3. **Update environment variables:**
```bash
# Edit production config
nano .env.production
```

4. **Deploy:**
```bash
# Using systemd
sudo systemctl restart lumiere

# Or using Docker Compose
docker compose -f docker-compose.production.yaml up -d
```

5. **Verify deployment:**
```bash
# Health check
curl https://api.lumiere.trade/health

# Check logs
sudo journalctl -u lumiere -f --since "5 minutes ago"
```

---

## Debugging

### Common Issues

#### Issue: Database Connection Failed

**Symptoms:**
- Service won't start
- "Connection refused" errors
- `psycopg2.OperationalError`

**Diagnosis:**
```bash
# Check PostgreSQL running
sudo systemctl status postgresql

# Check connection string
echo $DATABASE_URL

# Test connection manually
psql $DATABASE_URL
```

**Solutions:**
```bash
# Start PostgreSQL
sudo systemctl start postgresql

# Fix connection string in .env.development
DATABASE_URL=postgresql://lumiere_dev:password@localhost:5432/lumiere_pourtier

# Check PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-16-main.log
```

---

#### Issue: Redis Connection Failed

**Symptoms:**
- Cache operations fail
- 502 Bad Gateway errors
- "Connection refused to Redis"

**Diagnosis:**
```bash
# Check Redis running
redis-cli ping
# Expected: PONG

# Check Redis status
sudo systemctl status redis-server
```

**Solutions:**
```bash
# Start Redis
sudo systemctl start redis-server

# Check Redis logs
sudo tail -f /var/log/redis/redis-server.log

# Test connection
redis-cli -h localhost -p 6379 ping
```

---

#### Issue: Import Errors

**Symptoms:**
- `ModuleNotFoundError: No module named 'pourtier'`
- `ImportError: cannot import name 'X'`

**Solutions:**
```bash
# Reinstall package in editable mode
pip install -e .

# Verify installation
pip show pourtier

# Check PYTHONPATH
echo $PYTHONPATH

# Verify src layout
ls -la src/pourtier/
```

---

#### Issue: Docker Build Fails

**Symptoms:**
- "COPY failed" errors
- "No such file or directory"
- BuildX errors

**Diagnosis:**
```bash
# Check Docker BuildX
docker buildx ls

# Check builder active
docker buildx inspect lumiere-builder
```

**Solutions:**
```bash
# Create BuildX builder if missing
docker buildx create --name lumiere-builder --driver docker-container --bootstrap
docker buildx use lumiere-builder

# Clean Docker cache
docker builder prune -a -f

# Rebuild
cd ~/lumiere/lumiere-backend
docker buildx build -f pourtier/Dockerfile --target development -t pourtier:development --load .
```

---

### Debugging Tools

**Interactive debugger:**
```python
# Add breakpoint in code
import pdb; pdb.set_trace()

# Or use built-in breakpoint()
breakpoint()
```

**Logging:**
```python
import logging
logger = logging.getLogger(__name__)

logger.debug("Detailed debug information")
logger.info("General information")
logger.warning("Warning message")
logger.error("Error occurred", exc_info=True)  # Include traceback
```

**Database query logging:**
```yaml
# config/development.yaml
database:
  echo: true  # Log all SQL queries
```

**HTTP request logging:**
```python
# Log all HTTP requests to Passeur
import httpx

async with httpx.AsyncClient() as client:
    response = await client.get(url)
    logger.info(f"Request: {response.request.method} {response.request.url}")
    logger.info(f"Response: {response.status_code}")
```

---

## Useful Commands

### Database
```bash
# Connect to database
psql lumiere_pourtier

# List tables
\dt

# Describe table
\d users

# Run migration
alembic upgrade head

# Rollback migration
alembic downgrade -1

# Create new migration
alembic revision --autogenerate -m "add_user_preferences_table"

# Show migration history
alembic history

# Show current version
alembic current
```

---

### Docker
```bash
# View logs
docker logs lumiere-pourtier -f

# Execute command in container
docker exec -it lumiere-pourtier bash

# Inspect container
docker inspect lumiere-pourtier

# Check resource usage
docker stats lumiere-pourtier

# Restart container
docker restart lumiere-pourtier

# Clean up stopped containers
docker container prune

# Clean up unused images
docker image prune -a

# Check disk usage
docker system df
```

---

### Service Management
```bash
# Check service status
sudo systemctl status lumiere-dev

# View logs (last 100 lines)
sudo journalctl -u lumiere-dev -n 100

# Follow logs
sudo journalctl -u lumiere-dev -f

# Restart service
sudo systemctl restart lumiere-dev

# Stop service
sudo systemctl stop lumiere-dev

# Disable auto-start
sudo systemctl disable lumiere-dev
```

---

## Next Steps

After setup is complete:

1. **Read architecture docs:**
   - [ARCHITECTURE.md](ARCHITECTURE.md) - System design
   - [API_REFERENCE.md](API_REFERENCE.md) - API endpoints

2. **Explore codebase:**
   - Domain layer: `src/pourtier/domain/`
   - Use cases: `src/pourtier/application/use_cases/`
   - API routes: `src/pourtier/presentation/api/routes/`

3. **Check pending work:**
   - [TODO list](../todo/) - Pending tasks

4. **Join communication channels:**
   - GitHub Discussions
   - Project Discord (if available)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | October 27, 2025 | Initial development guide |

---

**Approved By:** Vladimir (Solo Founder)  
**Next Review:** January 27, 2026

---

**END OF DOCUMENT**

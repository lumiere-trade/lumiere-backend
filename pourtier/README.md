# Pourtier - User Management & Subscription Service

**FastAPI-based user management with Solana wallet authentication and subscription handling.**

---

## Overview

Pourtier is the user-facing API layer of Lumiere, handling:
- Wallet-based authentication (passwordless)
- User profiles and KYC compliance
- Subscription management (Basic/Pro tiers)
- Escrow account initialization
- Legal document acceptance tracking

**Architecture:** Clean Architecture / Hexagonal Architecture

---

## Features

### Authentication
- Solana wallet signature verification
- JWT token-based sessions
- No passwords (wallet = identity)
- Automatic token refresh

### Subscriptions
- Basic Plan: Single strategy deployment
- Pro Plan: Unlimited strategies + advanced features
- Payment via escrow balance
- Automatic expiration handling

### Performance
- Multi-layer caching (L1 memory + L2 Redis)
- Prometheus metrics
- Connection pooling
- Response caching

### Monitoring
- Prometheus `/metrics` endpoint
- Health check `/health`
- Structured JSON logging
- Request ID tracking

---

## Architecture
```
presentation/          # API Layer
├── api/
│   ├── routes/       # FastAPI endpoints
│   ├── schemas/      # Pydantic models
│   └── middleware/   # Auth, metrics, logging

application/          # Use Cases
├── use_cases/        # Business workflows
└── dto/             # Data transfer objects

domain/              # Core Business Logic
├── entities/        # User, Subscription
├── value_objects/   # WalletAddress, SubscriptionPlan
├── repositories/    # Repository interfaces
└── services/        # Domain service interfaces

infrastructure/      # External Integrations
├── persistence/     # PostgreSQL (SQLAlchemy)
├── cache/          # Redis multi-layer cache
├── blockchain/     # Solana integration
├── auth/           # JWT, wallet verification
└── monitoring/     # Prometheus, logging

di/                 # Dependency Injection
└── container.py    # Service container
```

---

## Quick Start

### Prerequisites
```bash
# System requirements
Python 3.11+
PostgreSQL 16+
Redis 7+
```

### Installation
```bash
# Install dependencies
pip install -e .

# Setup database
python pourtier/scripts/init_database.py

# Seed initial legal documents
python pourtier/scripts/seed_initial_terms.py
```

### Configuration

Create `pourtier/config/pourtier.yaml`:
```yaml
# Database
DATABASE_URL: "postgresql+asyncpg://user:pass@localhost:5432/pourtier_db"

# Redis
REDIS_HOST: "localhost"
REDIS_PORT: 6379
REDIS_PASSWORD: null  # Optional

# JWT
JWT_SECRET_KEY: "your-secret-key-here"
JWT_ALGORITHM: "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES: 30

# Blockchain
SOLANA_RPC_URL: "https://api.devnet.solana.com"
ESCROW_PROGRAM_ID: "your-program-id"

# Services
PASSEUR_URL: "http://localhost:8767"
COURIER_URL: "ws://localhost:8766"

# Environment
ENV: "development"
```

### Run
```bash
# Development
python -m pourtier.main

# API available at http://localhost:9000
```

---

## API Endpoints

### Authentication
```bash
POST   /api/auth/verify          # Verify wallet signature
POST   /api/auth/register         # Create account + accept legal docs
POST   /api/auth/login            # Login existing user
```

### Users
```bash
GET    /api/users/me              # Get current user profile
GET    /api/users/{user_id}       # Get user by ID
PATCH  /api/users/me              # Update profile
```

### Subscriptions
```bash
POST   /api/subscriptions/        # Create subscription
GET    /api/subscriptions/        # List user subscriptions
GET    /api/subscriptions/{id}    # Get subscription details
DELETE /api/subscriptions/{id}    # Cancel subscription
```

### Escrow
```bash
POST   /api/escrow/initialize     # Initialize escrow account
POST   /api/escrow/deposit        # Deposit funds (background job)
POST   /api/escrow/withdraw       # Withdraw funds (background job)
GET    /api/escrow/balance        # Get current balance
```

### Legal
```bash
GET    /api/legal/documents       # Get active legal documents
POST   /api/legal/accept          # Accept legal documents
GET    /api/legal/compliance      # Check user compliance
```

### Health & Metrics
```bash
GET    /health                    # Service health check
GET    /metrics                   # Prometheus metrics
```

---

## Testing
```bash
# Run all tests
laborant pourtier --integration

# Run specific test file
python -m pourtier.tests.integration.api.test_auth_routes

# With coverage
pytest pourtier/tests/ --cov=pourtier --cov-report=html
```

**Current Test Coverage:**
- User routes: 13/13 passing
- Auth routes: 14/14 passing
- Subscription routes: 15/15 passing

---

## Development

### Code Standards

- **PEP8 compliant** (use `black` formatter)
- **Type hints** for all functions
- **Docstrings** with Args/Returns/Raises
- **Max line length:** 88 characters

### Database Schema

Database schema is managed via SQL scripts:
```bash
# Create tables
psql -U pourtier_user -d pourtier_db -f pourtier/infrastructure/persistence/schema.sql

# Or use Python script
python pourtier/scripts/init_database.py
```

### Performance Optimization

**Phase 1-5 Complete:**
1. Connection pooling (20 connections)
2. Response caching (Redis)
3. Query optimization (eager loading)
4. Monitoring (Prometheus + structured logging)
5. Multi-layer caching (L1 + L2)

**Results:**
- User lookups: 25-45x faster with cache
- Database load: 80-95% reduction
- API response times: <100ms (cached)

---

## Monitoring

### Prometheus Metrics
```
# HTTP metrics
pourtier_http_requests_total
pourtier_http_request_duration_seconds

# Database metrics
pourtier_db_queries_total
pourtier_db_connection_pool_size

# Cache metrics
pourtier_cache_hits_total{cache_type="L1|L2"}
pourtier_cache_misses_total

# Business metrics
pourtier_users_active_total
pourtier_subscriptions_active_total
```

### Structured Logging
```json
{
  "timestamp": "2025-10-16T12:34:56.789Z",
  "level": "INFO",
  "message": "User authenticated",
  "request_id": "abc-123-def-456",
  "user_id": "uuid",
  "wallet": "wallet-address"
}
```

---

## Security

### Authentication Flow

1. User signs message with Solana wallet
2. Backend verifies signature with public key
3. JWT token issued (30min expiry)
4. Token used for subsequent requests

### Best Practices

- No passwords stored
- JWT tokens expire automatically
- Wallet signatures verify ownership
- SQL injection protection (parameterized queries)
- CORS configured properly
- Rate limiting (planned)

---

## Contributing

See main [CONTRIBUTING.md](../CONTRIBUTING.md)

### Running Locally

1. Fork & clone repository
2. Setup virtual environment
3. Install dependencies
4. Create `config/pourtier.yaml`
5. Run database setup scripts
6. Start services (PostgreSQL, Redis)
7. Run `python -m pourtier.main`

---

## License

Apache License 2.0 - See [LICENSE](../LICENSE)

---

## Related Components

- [Passeur](../passeur) - Blockchain bridge
- [Courier](../courier) - Event bus
- [Smart Contracts](../smart_contracts) - Escrow contracts

---

**Questions?** Open an issue or contact: dev@lumiere.trade

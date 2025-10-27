# Pourtier Architecture

**Version:** 1.0  
**Date:** October 27, 2025  
**Status:** Active  
**Component Type:** User Management & Authentication Service

---

## Table of Contents

1. [System Context](#system-context)
2. [Component Responsibilities](#component-responsibilities)
3. [Clean Architecture Layers](#clean-architecture-layers)
4. [Key Design Decisions](#key-design-decisions)
5. [Integration Patterns](#integration-patterns)
6. [Technology Stack](#technology-stack)
7. [Data Flow](#data-flow)
8. [Performance Considerations](#performance-considerations)
9. [Security Model](#security-model)
10. [Future Considerations](#future-considerations)

---

## System Context

### Position in Lumiere Ecosystem
```
Frontend (Next.js/React)
         │
         │ HTTPS/REST
         ▼
    ┌─────────────┐
    │  POURTIER   │ ◄─────── API Gateway & User Management
    │   (9000)    │
    └──────┬──────┘
           │
           ├──────────────┬──────────────┬──────────────┐
           │              │              │              │
           ▼              ▼              ▼              ▼
      ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌──────────┐
      │Passeur  │   │Architect│   │Courier  │   │PostgreSQL│
      │ (9003)  │   │ (9004)  │   │(WS/Redis│   │ (5432)   │
      │Escrow   │   │Strategy │   │Pub/Sub) │   │Persistence│
      └─────────┘   └─────────┘   └─────────┘   └──────────┘
```

Pourtier is the **primary entry point** for all user-facing operations on the Lumiere platform.

### Dependencies

**Upstream (services Pourtier depends on):**
- PostgreSQL 16 - User data persistence
- Redis 7 - L2 distributed cache
- Passeur - Escrow balance queries and initialization

**Downstream (services that depend on Pourtier):**
- Frontend - All user operations
- Architect - User validation for strategy deployment
- Chevalier - User subscription verification

**External:**
- Solana RPC - Wallet signature verification
- Courier (Redis Pub/Sub) - Event publishing

---

## Component Responsibilities

### Primary Responsibilities

**Authentication & Authorization:**
- Wallet-based authentication (no passwords)
- Message signature verification (Solana ed25519)
- JWT token generation and validation
- Session management (30-minute token expiry)
- Protected route middleware

**User Management:**
- User registration (wallet-based)
- Profile management (display name, email)
- Wallet address tracking
- User lifecycle management

**Subscription Management:**
- Subscription plan handling (Free/Basic/Pro)
- Plan limits enforcement (active strategies, backtests)
- Escrow-based billing (deduct from Passeur balance)
- Subscription status tracking (active/expired/cancelled)

**Legal Compliance:**
- Legal document management (TOS, Privacy Policy, Risk Disclosure)
- User acceptance tracking with timestamps
- Compliance validation before strategy deployment
- IP address logging for acceptance audit trail

**Escrow Coordination:**
- Proxy to Passeur for balance queries
- Escrow initialization requests
- Transaction history retrieval

### NOT Responsible For

- ❌ **Wallet custody** - Users control private keys
- ❌ **Trading execution** - That's Chevalier's responsibility
- ❌ **Strategy storage** - That's Architect's responsibility
- ❌ **Market data** - That's Chronicler's responsibility
- ❌ **Blockchain operations** - That's Passeur's responsibility

### Bounded Context (DDD)

**Context Name:** User Identity & Subscription Management

**Context Boundary:**
- Starts: User connects wallet
- Ends: User identity validated, subscription verified
- Domain: User accounts, subscriptions, legal compliance

---

## Clean Architecture Layers
```
┌─────────────────────────────────────────────────────────────┐
│                   PRESENTATION LAYER                         │
│                    (FastAPI Routes)                          │
│                                                              │
│  /api/auth/*      /api/users/*      /api/subscriptions/*    │
│  /api/legal/*     /api/escrow/*     /api/validate/*         │
│                                                              │
│  - Request validation (Pydantic schemas)                     │
│  - Response formatting (DTOs)                                │
│  - JWT authentication middleware                             │
│  - Error handling & logging                                  │
└──────────────────────────┬───────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────┐
│                   APPLICATION LAYER                          │
│                      (Use Cases)                             │
│                                                              │
│  CreateUser            AuthenticateWallet                    │
│  CreateSubscription    CheckUserLegalCompliance             │
│  ValidateDeployment    GetEscrowBalance                      │
│                                                              │
│  - Business workflow orchestration                           │
│  - Transaction management                                    │
│  - Event publishing (via Courier)                            │
│  - Cross-aggregate coordination                              │
└──────────────────────────┬───────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────┐
│                     DOMAIN LAYER                             │
│                  (Business Logic)                            │
│                                                              │
│  Entities:          Value Objects:         Domain Events:    │
│  - User             - WalletAddress        - UserCreated     │
│  - Subscription     - SubscriptionPlan     - SubscriptionActivated│
│  - LegalDocument    - EscrowBalance        - LegalDocumentAccepted│
│                                                              │
│  Business Rules:                                             │
│  - Wallet address must be valid Solana address               │
│  - User must accept all legal documents before trading       │
│  - Strategy deployment requires active subscription          │
│  - Subscription billing requires sufficient escrow balance   │
└──────────────────────────┬───────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────┐
│                 INFRASTRUCTURE LAYER                         │
│              (External Integrations)                         │
│                                                              │
│  Repositories:        Services:           Cache:             │
│  - UserRepository     - PasseurService    - CacheService     │
│  - SubscriptionRepo   - CourierService    (L1 Memory +      │
│  - LegalDocumentRepo  - JWTService        L2 Redis)          │
│                                                              │
│  Persistence:         External APIs:      Events:            │
│  - PostgreSQL         - Solana RPC        - Courier          │
│  - SQLAlchemy ORM     - Passeur HTTP      (Redis Pub/Sub)    │
└──────────────────────────────────────────────────────────────┘
```

### Layer Descriptions

**Presentation Layer (FastAPI):**
- Handles HTTP requests/responses
- Request validation using Pydantic schemas
- JWT token extraction and validation
- Response formatting and error handling
- No business logic - only request/response translation

**Application Layer (Use Cases):**
- Orchestrates domain entities to fulfill use cases
- Manages transactions across repositories
- Publishes domain events to Courier
- Coordinates between aggregates
- Contains NO domain logic - only workflow coordination

**Domain Layer (Core Business):**
- Pure business logic with NO infrastructure dependencies
- Entity validation rules
- Value object immutability
- Domain events definition
- Business invariants enforcement

**Infrastructure Layer (Adapters):**
- PostgreSQL via SQLAlchemy ORM
- Redis caching (multi-layer L1 + L2)
- Passeur HTTP client (escrow operations)
- Courier event publishing (Redis Pub/Sub)
- JWT token generation/validation

### Dependency Rule

**Golden Rule:** Dependencies point **inward only**
```
Presentation → Application → Domain ← Infrastructure
    ↓              ↓            ↑          ↑
  (uses)        (uses)     (defines)  (implements)
```

- **Domain** defines interfaces (ports)
- **Infrastructure** implements interfaces (adapters)
- **Application** uses domain and infrastructure through interfaces
- **Presentation** calls application use cases

---

## Key Design Decisions

### Decision 1: Wallet-Based Authentication (No Passwords)

**Date:** 2025-09-15  
**Status:** Accepted  
**Deciders:** Vladimir (Solo Founder)

**Context:**
Traditional password-based authentication creates security risks (password breaches, weak passwords, credential stuffing). Lumiere targets crypto-native users who already have Solana wallets.

**Decision:**
Use Solana wallet signature verification for passwordless authentication.

**Flow:**
1. User requests nonce from backend
2. User signs nonce with wallet private key
3. Backend verifies signature using wallet's public key
4. Backend issues JWT token for session management

**Rationale:**
- **Security:** No password database to breach
- **UX:** Users already have wallets, no new credentials
- **Blockchain-native:** Aligns with Web3 identity principles
- **Industry Standard:** Used by Uniswap, Jupiter, Raydium

**Consequences:**

**Positive:**
- No password management complexity
- Strong cryptographic security (ed25519)
- Simplified user experience
- No "forgot password" flows
- Users maintain custody of identity

**Negative:**
- Users must have Solana wallet installed
- Signature UX can be confusing for non-crypto users
- Wallet loss = account loss (mitigated by social recovery)
- Limited to Solana ecosystem initially

**Alternatives Considered:**

1. **Email/Password + 2FA**
   - Rejected: Security risk, password breaches
   - Rejected: Not crypto-native, poor UX for target audience

2. **OAuth (Google/Twitter)**
   - Rejected: Centralized identity, goes against Web3 principles
   - Rejected: Users don't control identity

3. **Magic Links**
   - Rejected: Email dependency, not wallet-based
   - Rejected: Doesn't align with blockchain ecosystem

---

### Decision 2: Clean Architecture / Hexagonal Architecture

**Date:** 2025-09-20  
**Status:** Accepted  
**Deciders:** Vladimir (Solo Founder)

**Context:**
Need maintainable, testable codebase that can evolve as requirements change. Must separate business logic from infrastructure concerns.

**Decision:**
Implement Clean Architecture with strict layer separation: Domain → Application → Infrastructure → Presentation.

**Rationale:**
- **Testability:** Domain logic testable without database/HTTP
- **Maintainability:** Clear boundaries, easy to understand
- **Flexibility:** Can swap PostgreSQL for MongoDB without changing domain
- **Industry Standard:** Used by Uncle Bob, Netflix, Amazon

**Consequences:**

**Positive:**
- High test coverage (98% with Laborant)
- Easy to swap infrastructure (e.g., change cache provider)
- Clear separation of concerns
- New developers understand structure quickly
- Domain logic independent of frameworks

**Negative:**
- More files/folders than "simple" architecture
- Steeper learning curve for junior developers
- Requires discipline to maintain boundaries
- More boilerplate for simple CRUD operations

**Alternatives Considered:**

1. **Layered Architecture (Controller → Service → Repository)**
   - Rejected: Business logic leaks into service layer
   - Rejected: Tight coupling to infrastructure

2. **Transaction Script (procedural style)**
   - Rejected: Not maintainable at scale
   - Rejected: Hard to test, all logic in routes

3. **Microkernel Architecture**
   - Rejected: Overkill for single service
   - Rejected: Adds unnecessary complexity

---

### Decision 3: Multi-Layer Caching (L1 Memory + L2 Redis)

**Date:** 2025-10-01  
**Status:** Accepted  
**Deciders:** Vladimir (Solo Founder)

**Context:**
User profile and subscription lookups are frequent operations. Database queries for every request create latency and load. Need sub-100ms response times.

**Decision:**
Implement two-tier caching:
- **L1 Cache:** In-memory Python dict (ultra-fast, single instance)
- **L2 Cache:** Redis (distributed, shared across instances)

**Cache Strategy:**
- Read-through: Check L1 → L2 → Database
- Write-through: Update database → invalidate L1 & L2
- TTL: 5 minutes for user profiles, 1 minute for subscriptions

**Rationale:**
- **Performance:** 25-45x faster than database queries
- **Scalability:** Reduces database load by 80-95%
- **Cost:** Fewer database connections needed
- **Reliability:** L1 fallback if Redis fails (graceful degradation)

**Consequences:**

**Positive:**
- API latency: 50-100ms (cached) vs 300-500ms (database)
- Database CPU usage: 20% (with cache) vs 80% (without)
- Can handle 10x more requests with same hardware
- Horizontal scaling easier (Redis shared state)

**Negative:**
- Cache invalidation complexity (must invalidate on all writes)
- Eventual consistency (5-minute max staleness)
- Memory usage for L1 cache (bounded by max entries)
- Redis becomes single point of failure (mitigated by L1 fallback)

**Alternatives Considered:**

1. **Redis Only (No L1)**
   - Rejected: Redis network latency (1-5ms) still slower than memory (<0.1ms)
   - Rejected: Single point of failure without L1 fallback

2. **Database Query Optimization Only**
   - Rejected: Can't beat cache performance, even with perfect indexes
   - Rejected: Doesn't scale horizontally

3. **CDN Caching (Cloudflare)**
   - Rejected: Not suitable for authenticated user data
   - Rejected: Doesn't cache POST/PUT requests

---

### Decision 4: Escrow-Based Subscription Billing

**Date:** 2025-09-25  
**Status:** Accepted  
**Deciders:** Vladimir (Solo Founder)

**Context:**
Subscription billing traditionally uses Stripe/credit cards. Lumiere targets crypto-native users who prefer on-chain payments and non-custodial fund management.

**Decision:**
Deduct subscription fees directly from user's Passeur escrow balance (USDC). No credit cards, no Stripe.

**Flow:**
1. User deposits USDC to Passeur escrow
2. Monthly subscription fee (e.g., $29) deducted from escrow
3. If insufficient balance, subscription expires
4. User can top up escrow anytime to reactivate

**Rationale:**
- **Non-custodial:** Users control funds, not platform
- **Transparent:** On-chain payment verification
- **Crypto-native:** No fiat on-ramps needed
- **Lower Fees:** No Stripe 2.9% + 30¢ fee

**Consequences:**

**Positive:**
- User trust (non-custodial approach)
- Simplified payment flow (no credit card forms)
- No PCI compliance requirements
- Lower payment processing costs
- Blockchain-native transparency

**Negative:**
- Users must have USDC in escrow
- Cannot serve users without crypto
- Subscription management more complex (check balances)
- Refunds require on-chain transactions

**Alternatives Considered:**

1. **Stripe + Credit Cards**
   - Rejected: Custodial approach, users don't trust
   - Rejected: High fees (2.9% + 30¢)
   - Rejected: Not crypto-native

2. **Lightning Network (Bitcoin)**
   - Rejected: Lumiere is Solana-native, not Bitcoin
   - Rejected: Adds complexity of multi-chain support

3. **Free Forever (No Subscriptions)**
   - Rejected: Not sustainable business model
   - Rejected: Cannot fund development long-term

---

### Decision 5: Legal Compliance Tracking

**Date:** 2025-10-05  
**Status:** Accepted  
**Deciders:** Vladimir (Solo Founder)

**Context:**
Regulatory compliance requires explicit user consent for Terms of Service, Privacy Policy, and Risk Disclosure. Must have audit trail proving user acceptance.

**Decision:**
Store legal document acceptance in database with timestamps and IP addresses. Block strategy deployment if user hasn't accepted all required documents.

**Schema:**
```sql
user_legal_acceptances (
  user_id,
  document_id,
  accepted_at,
  ip_address
)
```

**Rationale:**
- **Legal Protection:** Proof of user consent
- **Regulatory Compliance:** Meets SEC/CFTC requirements
- **Risk Mitigation:** Clear audit trail for disputes

**Consequences:**

**Positive:**
- Legal defensibility in disputes
- Regulatory compliance
- Clear audit trail
- Can update legal documents and re-prompt users

**Negative:**
- Extra database tables and queries
- UX friction (users must accept documents)
- Complexity in tracking multiple document versions

**Alternatives Considered:**

1. **Clickwrap Only (No Database Tracking)**
   - Rejected: No audit trail, legal risk
   - Rejected: Cannot prove acceptance in disputes

2. **Blockchain-Based Acceptance (Sign on-chain)**
   - Rejected: High gas fees for simple acceptance
   - Rejected: Overkill for compliance tracking

---

## Integration Patterns

### HTTP APIs (Synchronous)

**Passeur Integration:**
```python
# Pourtier → Passeur (HTTP REST)
class PasseurService:
    def get_escrow_balance(user_wallet: str) -> Decimal:
        response = httpx.get(f"{PASSEUR_URL}/escrow/{user_wallet}/balance")
        return Decimal(response.json()["balance"])
```

**Pattern:** Synchronous HTTP with retry logic and circuit breaker

**Error Handling:**
- Retry 3 times with exponential backoff (1s, 2s, 4s)
- Circuit breaker opens after 5 consecutive failures
- Fallback: Return cached balance or error to user

---

### Event-Driven Communication (Asynchronous)

**Courier Integration (Redis Pub/Sub):**
```python
# Pourtier publishes events
class CourierPublisher:
    def publish_user_created(user: User):
        event = {
            "event_type": "user.created",
            "user_id": str(user.id),
            "wallet_address": user.wallet_address,
            "timestamp": datetime.utcnow().isoformat()
        }
        redis.publish("lumiere.users", json.dumps(event))
```

**Published Events:**
- `user.created` → Chronicler (analytics), Mirror (notifications)
- `subscription.activated` → Architect (update user limits)
- `subscription.expired` → Chevalier (stop strategies)
- `legal_document.accepted` → Chronicler (compliance audit)

**Pattern:** Fire-and-forget event publishing (no response expected)

---

### Database Access

**PostgreSQL Connection Pooling:**
```python
# SQLAlchemy connection pool
engine = create_engine(
    DATABASE_URL,
    pool_size=20,           # 20 concurrent connections
    max_overflow=10,        # 10 extra connections if pool exhausted
    pool_pre_ping=True,     # Test connections before use
    pool_recycle=3600       # Recycle connections every hour
)
```

**Repository Pattern:**
```python
class UserRepository(IUserRepository):
    async def get_by_id(user_id: UUID) -> User:
        # Check cache first
        cached = cache_service.get(f"user:{user_id}")
        if cached:
            return User.from_dict(cached)
        
        # Query database
        user = await db.query(UserModel).filter_by(id=user_id).first()
        
        # Cache result
        cache_service.set(f"user:{user_id}", user.to_dict(), ttl=300)
        return user
```

---

### External Services

**Solana RPC (Wallet Signature Verification):**
```python
from solders.signature import Signature
from solders.pubkey import Pubkey

def verify_signature(message: str, signature: str, wallet: str) -> bool:
    message_bytes = message.encode('utf-8')
    signature_bytes = base58.b58decode(signature)
    pubkey = Pubkey.from_string(wallet)
    
    return Signature.verify(pubkey, message_bytes, signature_bytes)
```

---

## Technology Stack

### Core Technologies

**Language & Runtime:**
- Python 3.11+ (CPython)
- asyncio for async operations

**Web Framework:**
- FastAPI 0.104+ (async-first, auto OpenAPI docs)
- Uvicorn ASGI server (production-grade)
- Pydantic 2.0 (request/response validation)

**Database:**
- PostgreSQL 16 (primary persistence)
- SQLAlchemy 2.0 ORM (async support)
- Alembic (schema migrations)

**Cache:**
- Redis 7+ (L2 distributed cache)
- Python dict (L1 in-memory cache)

**Authentication:**
- PyJWT (JWT token generation/validation)
- passlib (if adding optional password support)
- solders (Solana signature verification)

### Key Libraries

**HTTP Client:**
- httpx (async HTTP client for Passeur calls)

**Event Publishing:**
- redis-py (Courier event publishing)

**Configuration:**
- PyYAML (YAML config loading)
- python-dotenv (environment variable loading)

**Testing:**
- pytest (test framework)
- pytest-asyncio (async test support)
- Custom Laborant framework (test orchestration)

**Logging:**
- SystemReporter (custom logging with Rich)
- structlog (structured logging for production)

### Infrastructure

**Containerization:**
- Docker (multi-stage builds)
- Docker Compose (local development)

**Service Management:**
- systemd (production service management)
- supervisord (alternative process manager)

**Reverse Proxy:**
- nginx (SSL termination, load balancing)
- Let's Encrypt (SSL certificates)

**Monitoring:**
- Prometheus metrics (future)
- Grafana dashboards (future)

---

## Data Flow

### Request Flow (REST API)

**Authenticated Request Example: GET /api/users/me**
```
1. Client Request
   ↓
   GET /api/users/me
   Authorization: Bearer eyJhbGc...
   
2. nginx (Reverse Proxy)
   ↓
   SSL termination
   Forward to Pourtier:9000
   
3. FastAPI Middleware
   ↓
   Extract JWT token
   Verify signature
   Extract user_id from token
   
4. Route Handler (Presentation Layer)
   ↓
   Call GetUserProfile use case
   
5. Use Case (Application Layer)
   ↓
   Call UserRepository.get_by_id()
   
6. Repository (Infrastructure Layer)
   ↓
   Check L1 cache (memory)
   ↓ (miss)
   Check L2 cache (Redis)
   ↓ (miss)
   Query PostgreSQL
   ↓
   Store in L2 & L1 cache
   
7. Response
   ↓
   Domain Entity → DTO (Pydantic)
   Return JSON response
```

**Latency Breakdown:**
- L1 cache hit: ~50ms total (0.1ms cache + 50ms network)
- L2 cache hit: ~80ms total (2ms Redis + 80ms network)
- Database hit: ~350ms total (250ms query + 100ms network)

---

### Event Flow (Async)

**Event Publishing Example: UserCreated**
```
1. Use Case Completes (Application Layer)
   ↓
   CreateUser.execute() finishes
   User entity persisted to database
   
2. Publish Domain Event
   ↓
   courier_service.publish(UserCreatedEvent)
   
3. Courier (Infrastructure Layer)
   ↓
   Serialize event to JSON
   redis.publish("lumiere.users", event_json)
   
4. Redis Pub/Sub Broadcast
   ↓
   Broadcast to all subscribers
   
5. Consumers (Other Services)
   ↓
   Chronicler: Store in analytics database
   Mirror: Send welcome notification
   
6. Pourtier Continues (Fire-and-forget)
   ↓
   Return success response to client
   (doesn't wait for consumers)
```

**Async Benefits:**
- Pourtier doesn't block on analytics/notifications
- Services decoupled (Chronicler down ≠ Pourtier down)
- Easy to add new consumers without changing Pourtier

---

## Performance Considerations

### Scalability

**Current Capacity:**
- Requests/second: 1,000+ (with caching)
- Concurrent users: 10,000+
- Database connections: 20 (pool size)

**Bottlenecks:**
- Database queries (mitigated by caching)
- Redis latency (2-5ms per operation)
- Passeur HTTP calls (100-300ms per request)

**Scaling Strategy:**
- **Horizontal:** Add more Pourtier instances behind nginx
- **Vertical:** Increase database connection pool
- **Caching:** L1/L2 cache reduces database load by 80-95%

**When to Scale:**
- CPU > 70% sustained
- Database connection pool exhausted
- Response time > 500ms (p95)

---

### Caching Strategy

**What is Cached:**
- User profiles (TTL: 5 minutes)
- Subscription status (TTL: 1 minute)
- Legal document list (TTL: 1 hour)

**TTL Strategy:**
- Frequently changing: 1 minute (subscriptions)
- Moderately changing: 5 minutes (user profiles)
- Rarely changing: 1 hour (legal documents)

**Cache Invalidation:**
```python
# On user profile update
async def update_user(user_id: UUID, updates: dict):
    await db.update(user_id, updates)
    cache_service.delete(f"user:{user_id}")  # Invalidate L1 & L2
```

**Cache Warming:**
- On service startup, pre-warm cache with active users
- Reduces cold start latency

---

### Database Optimization

**Indexes:**
```sql
CREATE INDEX idx_users_wallet ON users(wallet_address);
CREATE INDEX idx_subscriptions_user_status ON subscriptions(user_id, status);
CREATE INDEX idx_legal_acceptances_user ON user_legal_acceptances(user_id);
```

**Query Optimization:**
- Use SQLAlchemy `joinedload()` to avoid N+1 queries
- Limit result sets with pagination
- Use `select_in_loading()` for collections

**Connection Pooling:**
- Pool size: 20 connections
- Max overflow: 10 additional connections
- Pool recycle: 1 hour (prevents stale connections)

---

## Security Model

### Authentication

**Method:** JWT with wallet signatures

**Token Structure:**
```json
{
  "user_id": "uuid",
  "wallet_address": "base58_address",
  "wallet_type": "Phantom",
  "exp": 1698364800,
  "iat": 1698361200
}
```

**Token Expiration:** 30 minutes

**Storage:** 
- Frontend: Memory only (not localStorage - XSS risk)
- Backend: Stateless (no token storage)

---

### Authorization

**Protected Routes:**
- All `/api/users/*` require valid JWT
- All `/api/subscriptions/*` require valid JWT
- Validation endpoints require internal API key

**Middleware:**
```python
@router.get("/api/users/me")
async def get_current_user(current_user: User = Depends(get_current_user)):
    return current_user
```

---

### Data Protection

**Sensitive Data:**
- Passwords: N/A (wallet-based auth)
- JWT secret: Environment variable, rotated quarterly
- API keys: Environment variable, never in code

**Encryption:**
- At rest: PostgreSQL full-disk encryption (LUKS)
- In transit: TLS 1.3 (Let's Encrypt certificates)

---

### Attack Mitigation

**SQL Injection:**
- Prevention: Parameterized queries (SQLAlchemy ORM)
- Never string concatenation for queries

**Rate Limiting:**
```python
# Redis-based rate limiting
@limiter.limit("100/minute")
async def create_user(...):
    ...
```

**CORS:**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://app.lumiere.trade"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
)
```

**Input Validation:**
- All requests validated with Pydantic schemas
- Wallet address format validation
- Email format validation
- Amount range validation

---

## Future Considerations

### Planned Improvements

**Rate Limiting V2:**
- Implement Redis-based distributed rate limiting
- Per-user and per-IP limits
- Automatic DDoS protection

**WebSocket Support:**
- Real-time subscription status updates
- Push notifications for legal document updates

**Multi-Chain Support:**
- Support Ethereum wallets (MetaMask)
- Support Bitcoin Lightning wallets

**Advanced Analytics:**
- User behavior tracking
- Subscription churn analysis
- A/B testing infrastructure

---

### Known Limitations

**Single-Chain Only:**
- Currently Solana-only
- Cannot authenticate non-Solana users

**Cache Staleness:**
- Up to 5 minutes stale data (acceptable for user profiles)
- Critical data (subscriptions) has 1-minute TTL

**No Multi-Tenancy:**
- Single Lumiere platform instance
- Cannot white-label for partners

---

### Roadmap Alignment

**Phase 1 (Current):** MVP with wallet auth, subscriptions
**Phase 2 (Q1 2026):** Rate limiting, WebSocket support
**Phase 3 (Q2 2026):** Multi-chain support, advanced analytics
**Phase 4 (Q3 2026):** White-label support, enterprise features

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | October 27, 2025 | Initial architecture document based on HLD v1.3 |

---

**Approved By:** Vladimir (Solo Founder)  
**Next Review:** January 27, 2026

---

**END OF DOCUMENT**

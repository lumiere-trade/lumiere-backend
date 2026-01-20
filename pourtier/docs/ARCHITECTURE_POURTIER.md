# Pourtier - API Gateway & User Management Layer

**Version:** 0.1.0
**Last Updated:** January 20, 2026
**Component Type:** API Gateway with Escrow-Based Subscription Management

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [System Architecture](#2-system-architecture)
3. [Core Components](#3-core-components)
4. [Data Flow & Execution](#4-data-flow--execution)
5. [Authentication & Authorization](#5-authentication--authorization)
6. [Escrow Management](#6-escrow-management)
7. [Deployment Architecture](#7-deployment-architecture)
8. [API Reference](#8-api-reference)
9. [Database Schema](#9-database-schema)
10. [Integration Points](#10-integration-points)
11. [Monitoring & Observability](#11-monitoring--observability)
12. [Troubleshooting Guide](#12-troubleshooting-guide)

---

## 1. Executive Summary

### 1.1 Purpose

Pourtier is Lumière's **API Gateway and User Management Layer** that handles authentication, subscription billing, and escrow management. It serves as the single entry point for all frontend requests and orchestrates communication between microservices using non-custodial blockchain escrow for payments.

### 1.2 Key Capabilities

- **Wallet-Based Authentication**: Solana wallet signature verification with JWT tokens
- **User Management**: Minimal Web3 identity (wallet address only)
- **Legal Compliance**: Terms of Service and Privacy Policy acceptance tracking
- **Escrow Management**: Non-custodial escrow accounts via Solana smart contracts
- **Subscription Billing**: Escrow-based SaaS subscriptions (Free, Basic, Pro)
- **API Gateway**: Routes requests to backend microservices (Prophet, Architect, Chevalier, etc.)
- **Resilience Patterns**: Circuit Breaker, Retry with Exponential Backoff, Rate Limiting, Idempotency
- **Multi-Layer Caching**: L1 (in-memory) + L2 (Redis) for user data
- **Real-Time Balance Queries**: Direct blockchain queries (no cached balances)

### 1.3 Architecture Principles

| Principle | Implementation |
|-----------|----------------|
| Non-Custodial | User controls funds via Solana escrow smart contract |
| Blockchain as Source of Truth | All balances queried real-time from blockchain |
| Prepare-Sign-Submit Pattern | Frontend signs transactions, backend submits via Passeur |
| Clean Architecture | Domain → Application → Infrastructure → Presentation |
| Idempotent Operations | All financial transactions protected by idempotency keys |
| Zero Trust | Every request authenticated via JWT + wallet signature |

### 1.4 Technology Stack

- **Runtime**: Python 3.11+ with FastAPI async/await
- **Database**: PostgreSQL (users, subscriptions, transactions)
- **Cache**: Redis (idempotency, rate limiting, L2 cache)
- **Blockchain**: Solana via Passeur Bridge (escrow smart contracts)
- **Authentication**: Ed25519 signature verification + JWT
- **Monitoring**: Prometheus metrics, dedicated health/metrics servers
- **Resilience**: Circuit Breaker (shared library), Retry, Rate Limiting

---

## 2. System Architecture

### 2.1 High-Level Architecture
```
┌─────────────────────────────────────────────────────────────────┐
│                   Frontend (Next.js)                            │
│                app.lumiere.trade                                │
│                                                                 │
│  User Flow:                                                     │
│  1. Connect Wallet (Phantom/Backpack/Solflare)                │
│  2. Sign Message → Verify Signature                            │
│  3. Login/Create Account → Get JWT Token                       │
│  4. Initialize Escrow (one-time)                               │
│  5. Deposit Funds → Blockchain Transaction                     │
│  6. Subscribe to Plan → Check Escrow Balance                   │
│  7. Use Platform → JWT Authentication                          │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTPS/REST + JWT Bearer Token
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                    Pourtier (This Component)                    │
│                     API Gateway (Port 9000)                     │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │           Presentation Layer (FastAPI)                   │  │
│  │                                                          │  │
│  │  Middleware Chain:                                       │  │
│  │  1. RequestIDMiddleware (tracking)                      │  │
│  │  2. MetricsMiddleware (Prometheus)                      │  │
│  │  3. RateLimitMiddleware (Redis token bucket)            │  │
│  │  4. GZipMiddleware (compression)                        │  │
│  │  5. CORSMiddleware (cross-origin)                       │  │
│  │                                                          │  │
│  │  Routes:                                                 │  │
│  │  /api/auth/*          - Authentication                  │  │
│  │  /api/users/*         - User management                 │  │
│  │  /api/escrow/*        - Escrow operations               │  │
│  │  /api/subscriptions/* - Subscription billing            │  │
│  │  /api/legal/*         - Legal documents                 │  │
│  │  /api/wallet/*        - Wallet balance queries          │  │
│  │  /api/prophet/*       - Prophet proxy                   │  │
│  │  /api/architect/*     - Architect proxy                 │  │
│  │  /api/chevalier/*     - Chevalier proxy                 │  │
│  │  /api/cartographe/*   - Cartographe proxy               │  │
│  │  /api/chronicler/*    - Chronicler proxy                │  │
│  │  /api/tsdl/*          - TSDL proxy                      │  │
│  └──────────────────────┬───────────────────────────────────┘  │
│                         │                                       │
│  ┌──────────────────────▼───────────────────────────────────┐  │
│  │         Application Layer (Use Cases)                    │  │
│  │                                                          │  │
│  │  Authentication:                                         │  │
│  │  - VerifyWalletSignature                                │  │
│  │  - CreateUserWithLegal                                  │  │
│  │  - LoginUser                                            │  │
│  │                                                          │  │
│  │  Escrow Management:                                      │  │
│  │  - PrepareInitializeEscrow (unsigned tx)                │  │
│  │  - InitializeEscrow (submit signed tx)                  │  │
│  │  - PrepareDeposit (unsigned tx)                         │  │
│  │  - DepositToEscrow (submit signed tx)                   │  │
│  │  - PrepareWithdraw (unsigned tx)                        │  │
│  │  - WithdrawFromEscrow (submit signed tx)                │  │
│  │  - GetEscrowBalance (blockchain query)                  │  │
│  │                                                          │  │
│  │  Subscription:                                           │  │
│  │  - CreateSubscription                                   │  │
│  │  - CheckSubscriptionStatus                              │  │
│  │                                                          │  │
│  │  User Management:                                        │  │
│  │  - GetUserProfile                                       │  │
│  │  - UpdateUserProfile                                    │  │
│  └──────────────────────┬───────────────────────────────────┘  │
│                         │                                       │
│  ┌──────────────────────▼───────────────────────────────────┐  │
│  │              Domain Layer                                │  │
│  │                                                          │  │
│  │  Entities:                                               │  │
│  │  - User (id, wallet_address, created_at)                │  │
│  │  - Subscription (plan, status, expires_at)              │  │
│  │  - EscrowTransaction (tx_signature, amount, status)     │  │
│  │  - LegalDocument (type, version, content)               │  │
│  │  - UserLegalAcceptance (user, document, accepted_at)    │  │
│  │                                                          │  │
│  │  Repositories (Interfaces):                             │  │
│  │  - IUserRepository                                      │  │
│  │  - ISubscriptionRepository                              │  │
│  │  - IEscrowTransactionRepository                         │  │
│  │  - ILegalDocumentRepository                             │  │
│  │  - IUserLegalAcceptanceRepository                       │  │
│  │                                                          │  │
│  │  Services (Interfaces):                                 │  │
│  │  - IWalletAuthenticator (signature verification)        │  │
│  │  - IPasseurBridge (blockchain transactions)             │  │
│  │  - IEscrowQueryService (balance queries)                │  │
│  │  - IBlockchainVerifier (tx confirmation)                │  │
│  │  - IEventPublisher (Courier integration)                │  │
│  └──────────────────────┬───────────────────────────────────┘  │
│                         │                                       │
│  ┌──────────────────────▼───────────────────────────────────┐  │
│  │         Infrastructure Layer                             │  │
│  │                                                          │  │
│  │  Persistence:                                            │  │
│  │  - Database (SQLAlchemy + asyncpg)                      │  │
│  │  - UserRepository (with L1+L2 cache)                    │  │
│  │  - SubscriptionRepository                               │  │
│  │  - EscrowTransactionRepository                          │  │
│  │  - LegalDocumentRepository                              │  │
│  │  - UserLegalAcceptanceRepository                        │  │
│  │                                                          │  │
│  │  Blockchain:                                             │  │
│  │  - PasseurBridgeClient (HTTP → Passeur)                │  │
│  │  - PasseurQueryService (balance queries)                │  │
│  │  - SolanaTransactionVerifier (tx confirmation)          │  │
│  │  - EscrowContractClient (smart contract wrapper)        │  │
│  │                                                          │  │
│  │  Authentication:                                         │  │
│  │  - SolanaWalletAdapter (Ed25519 verification)           │  │
│  │  - JWTHandler (token creation/validation)               │  │
│  │                                                          │  │
│  │  Caching:                                                │  │
│  │  - RedisCacheClient (Redis connection)                  │  │
│  │  - MultiLayerCache (L1 in-memory + L2 Redis)           │  │
│  │  - RedisIdempotencyStore (financial ops)                │  │
│  │                                                          │  │
│  │  Resilience:                                             │  │
│  │  - CircuitBreaker (Passeur calls)                       │  │
│  │  - Retry (exponential backoff + jitter)                 │  │
│  │  - RateLimiter (token bucket algorithm)                 │  │
│  │                                                          │  │
│  │  Event Bus:                                              │  │
│  │  - CourierPublisher (event broadcasting)                │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │           Monitoring Servers (Background)                │  │
│  │                                                          │  │
│  │  MetricsServer (port 9090):                             │  │
│  │  - /metrics → Prometheus format                         │  │
│  │  - Request counts, latencies, errors                    │  │
│  │  - Circuit breaker states                               │  │
│  │                                                          │  │
│  │  HealthServer (port 9091):                              │  │
│  │  - /health → Component health status                    │  │
│  │  - Database connectivity                                │  │
│  │  - Redis availability                                   │  │
│  │  - Connection pool stats                                │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
         │              │              │              │
         │              │              │              │
┌────────▼───┐  ┌──────▼──────┐  ┌───▼──────┐  ┌───▼────────┐
│ PostgreSQL │  │   Redis     │  │ Passeur  │  │  Courier   │
│ (Users,    │  │ (Cache,     │  │ (Solana  │  │ (Events)   │
│  Subscr.,  │  │  Idemp.,    │  │  Bridge) │  │            │
│  Escrow    │  │  Rate       │  │          │  │            │
│  Txns)     │  │  Limit)     │  │          │  │            │
└────────────┘  └─────────────┘  └──────────┘  └────────────┘
                                      │
                                      │
                              ┌───────▼────────┐
                              │ Solana Blockchain│
                              │ (Escrow Smart   │
                              │  Contracts)     │
                              └─────────────────┘
```

### 2.2 Component Interactions

**User Registration Flow:**
```
Frontend → POST /api/auth/verify (signature check)
    ↓
Pourtier.VerifyWalletSignature
    ↓
    1. SolanaWalletAdapter.verify_signature(wallet, message, signature)
    2. UserRepository.get_by_wallet(wallet)
    3. Return: {signature_valid: true, user_exists: false}
    ↓
Frontend → POST /api/auth/create-account (with legal acceptances)
    ↓
Pourtier.CreateUserWithLegal
    ↓
    1. Verify signature again
    2. Get all active legal documents
    3. Verify all documents accepted
    4. Create User entity
    5. Create UserLegalAcceptance records
    6. Generate JWT token
    7. Return: {access_token, user_id}
    ↓
Frontend stores JWT in localStorage
Frontend redirects to dashboard
```

**Escrow Initialization Flow (Prepare-Sign-Submit):**
```
Frontend → POST /api/escrow/prepare-initialize (with JWT)
    ↓
Pourtier.PrepareInitializeEscrow
    ↓
    1. Extract user_id from JWT
    2. Derive escrow PDA (deterministic)
    3. PasseurBridge.prepare_initialize_escrow(user_wallet)
    ↓
    Passeur generates unsigned transaction
    ↓
    Return: {transaction: "base64...", token_mint: "USDC"}
    ↓
Frontend shows transaction to user
User signs in wallet (Phantom/Backpack)
    ↓
Frontend → POST /api/escrow/initialize (with signed transaction)
    ↓
Pourtier.InitializeEscrow
    ↓
    1. Check idempotency key (prevent double init)
    2. PasseurBridge.submit_signed_transaction(signed_tx)
    ↓
    Passeur → Solana RPC (submit transaction)
    ↓
    Solana executes escrow::initialize instruction
    ↓
    3. Create EscrowTransaction record (INITIALIZE, confirmed)
    4. Return: {escrow_account, balance: 0, tx_signature}
```

**Subscription Creation Flow:**
```
Frontend → POST /api/subscriptions (plan_type: "basic", JWT)
    ↓
Pourtier.CreateSubscription
    ↓
    1. Get user from JWT
    2. Derive escrow PDA
    3. PasseurQueryService.check_escrow_exists(escrow_pda)
    4. PasseurQueryService.get_escrow_balance(escrow_pda)
    ↓
    Passeur → Solana RPC (query account data)
    ↓
    5. Verify balance >= plan price (e.g., 10 USDC for Basic)
    6. Create Subscription entity (ACTIVE, expires_at = now + 30 days)
    7. Save to PostgreSQL
    8. Return subscription
    ↓
Frontend updates UI with active subscription
```

---

## 3. Core Components

### 3.1 Domain Layer

#### 3.1.1 User Entity

**Purpose**: Minimal Web3 identity (immutable after creation).
```python
@dataclass
class User:
    id: UUID
    wallet_address: str  # Solana wallet (32-44 chars base58)
    created_at: datetime
    
    # NO email, NO display_name (optional in future)
    # NO escrow_account (derived from PDA, not stored)
    # NO escrow_balance (queried from blockchain)
```

**Business Rules:**
- Wallet address is unique (one user per wallet)
- Created once on first authentication
- Immutable (no updates except optional display_name in future)
- All financial data lives on blockchain, not in DB

#### 3.1.2 Subscription Entity

**Purpose**: SaaS subscription management with escrow billing.
```python
@dataclass
class Subscription:
    id: UUID
    user_id: UUID
    plan_type: SubscriptionPlan  # FREE, BASIC, PRO
    status: SubscriptionStatus    # ACTIVE, CANCELLED, EXPIRED
    started_at: datetime
    expires_at: Optional[datetime]  # None for FREE plan
    created_at: datetime
    updated_at: datetime
```

**Lifecycle:**
```
ACTIVE ───cancel()───► CANCELLED
  │
  └───expire()────► EXPIRED (auto by cron job)
  │
  └───renew()─────► ACTIVE (payment deducted from escrow)
```

**Plan Details:**
```python
FREE:   price=0,  duration=None,    features=[basic_backtesting]
BASIC:  price=10, duration=30_days, features=[live_trading, 5_strategies]
PRO:    price=50, duration=30_days, features=[live_trading, unlimited]
```

#### 3.1.3 EscrowTransaction Entity

**Purpose**: Audit trail for all escrow operations.
```python
@dataclass
class EscrowTransaction:
    id: UUID
    user_id: UUID
    tx_signature: str                # Solana tx signature (unique)
    transaction_type: TransactionType # INITIALIZE, DEPOSIT, WITHDRAW
    amount: Decimal
    token_mint: str                  # "USDC"
    status: TransactionStatus        # PENDING, CONFIRMED, FAILED
    subscription_id: Optional[UUID]  # Link to subscription (for fees)
    created_at: datetime
    confirmed_at: Optional[datetime]
```

**Transaction Types:**
- `INITIALIZE`: One-time escrow account creation (amount=0)
- `DEPOSIT`: User deposits USDC to escrow
- `WITHDRAW`: User withdraws USDC from escrow
- `SUBSCRIPTION_FEE`: Automatic deduction for subscription (future)

#### 3.1.4 LegalDocument Entity

**Purpose**: Platform legal documents (Terms, Privacy Policy).
```python
@dataclass
class LegalDocument:
    id: UUID
    document_type: DocumentType  # TERMS_OF_SERVICE, PRIVACY_POLICY
    version: str                 # "1.0.0"
    title: str
    content: str                 # Full text (Markdown)
    status: DocumentStatus       # DRAFT, ACTIVE, ARCHIVED
    effective_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime
```

**Versioning:**
- Only ONE active document per type at any time
- Old versions archived (audit trail)
- New users must accept all active documents
- Existing users see pending documents on login

#### 3.1.5 UserLegalAcceptance Entity

**Purpose**: Audit trail of legal acceptances.
```python
@dataclass
class UserLegalAcceptance:
    id: UUID
    user_id: UUID
    document_id: UUID
    accepted_at: datetime
    acceptance_method: AcceptanceMethod  # WEB_CHECKBOX, API_EXPLICIT
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: datetime
```

**Acceptance Methods:**
- `WEB_CHECKBOX`: User checked "I agree" box on frontend
- `API_EXPLICIT`: User called API with explicit acceptance
- `MIGRATION_IMPLICIT`: Existing users migrated (historical)

### 3.2 Infrastructure Layer

#### 3.2.1 PasseurBridgeClient

**Purpose**: HTTP client for Passeur Bridge API with resilience patterns.

**Key Features:**
- Circuit Breaker (prevents cascading failures to Passeur)
- Retry with Exponential Backoff + Jitter
- Prometheus Metrics (request counts, latencies, circuit state)
- Connection Pooling (50 total, 20 per host)
- Optimized Timeouts (30s total, 10s connect)

**Methods:**
```python
# Escrow Operations (Prepare-Sign-Submit Pattern)
async def prepare_initialize_escrow(user_wallet, token_mint) -> str
async def prepare_deposit(user_wallet, escrow, amount) -> str
async def prepare_withdraw(user_wallet, escrow, amount) -> str
async def submit_signed_transaction(signed_tx) -> str  # Returns signature

# Balance Queries
async def get_escrow_balance(escrow_account) -> Decimal
async def get_escrow_details(escrow_account) -> dict
async def get_wallet_balance(wallet_address) -> Decimal
```

**Circuit Breaker Config:**
```python
failure_threshold=5     # Open after 5 failures
success_threshold=2     # Close after 2 successes
timeout=60.0           # Stay open for 60s
```

**Retry Config:**
```python
max_attempts=3
initial_delay=1.0
max_delay=10.0
backoff_multiplier=2.0
jitter=True            # Randomize delays to prevent thundering herd
```

#### 3.2.2 SolanaWalletAdapter

**Purpose**: Ed25519 signature verification for wallet authentication.
```python
class SolanaWalletAdapter(IWalletAuthenticator):
    async def verify_signature(
        wallet_address: str,
        message: str,
        signature: str,
    ) -> bool:
        # 1. Decode wallet public key (base58 → bytes)
        # 2. Decode signature (base58 → bytes)
        # 3. Encode message (UTF-8 → bytes)
        # 4. Verify with Ed25519: verify_key.verify(message, signature)
        # 5. Return True/False
```

**Security:**
- Uses NaCl (libsodium) for cryptographic verification
- Prevents signature replay attacks (message includes timestamp)
- No private key handling (user signs in wallet)

#### 3.2.3 MultiLayerCache

**Purpose**: L1 (in-memory LRU) + L2 (Redis) caching for user data.

**Architecture:**
```python
class MultiLayerCache:
    L1: LRUCache (maxsize=1000, ttl=300s)   # Hot data
    L2: Redis (ttl=3600s)                    # Warm data
    
    async def get(key):
        # 1. Check L1 → Return if hit
        # 2. Check L2 → Populate L1 if hit
        # 3. Return None if both miss
    
    async def set(key, value):
        # 1. Store in L1 (with TTL)
        # 2. Store in L2 (with TTL)
```

**Cache Keys:**
```
user:wallet:{wallet_address}  → User entity
user:id:{user_id}             → User entity
subscription:{user_id}        → Active subscription
```

**Invalidation:**
- TTL-based (no manual invalidation)
- User updates are rare (wallet address immutable)
- Subscription updates trigger L1+L2 invalidation

#### 3.2.4 RedisIdempotencyStore

**Purpose**: Prevent duplicate financial transactions.

**Usage:**
```python
# Deposit idempotency
key = f"deposit:{user_id}:{amount}:{timestamp}"
cached = await idempotency_store.get_async(key)
if cached:
    return cached  # Already processed

result = await execute_deposit(...)
await idempotency_store.set_async(key, result, ttl=86400)  # 24 hours
```

**Key Format:**
```
idempotency:{operation}:{user_id}:{params}:{timestamp}
```

**TTL Strategy:**
- Financial ops: 24 hours (prevents same-day duplicates)
- Non-financial ops: 1 hour (shorter window)

### 3.3 Application Layer (Use Cases)

#### 3.3.1 CreateUserWithLegal

**Purpose**: Create user and record legal document acceptances atomically.

**Flow:**
```python
1. Verify wallet signature (Ed25519)
2. Check user doesn't exist
3. Get all active legal documents
4. Verify all documents accepted
5. Create User entity
6. Create UserLegalAcceptance records (one per document)
7. Return created user
```

**Error Handling:**
- Signature invalid → `ValidationError` (401)
- User exists → `ValidationError` (400)
- Missing document acceptances → `ValidationError` (400)

#### 3.3.2 InitializeEscrow (Idempotent)

**Purpose**: Initialize user's escrow account on blockchain.

**Idempotency Key:**
```python
f"initialize_escrow:{user_id}:{token_mint}"
```

**Flow:**
```python
1. Check idempotency (return cached if exists)
2. Get user from DB
3. Derive escrow PDA (deterministic)
4. Submit signed transaction to Passeur
   ↓ (Passeur → Solana RPC)
5. Create EscrowTransaction (INITIALIZE, confirmed)
6. Cache result (idempotency store, 24h)
7. Return (user, tx_signature)
```

**Critical:** Blockchain prevents duplicate initialization (account already exists error).

#### 3.3.3 DepositToEscrow (Idempotent)

**Purpose**: Deposit funds to escrow with duplicate prevention.

**Idempotency Key:**
```python
f"deposit:{user_id}:{amount}:{timestamp}"
```

**Flow:**
```python
1. Check idempotency (return cached if exists)
2. Get user from DB
3. Derive escrow PDA
4. Query blockchain: escrow exists?
5. Validate amount > 0
6. Submit signed transaction to Passeur
7. Check tx_signature not duplicate in DB
8. Create EscrowTransaction (DEPOSIT, confirmed)
9. Cache result (idempotency store, 24h)
10. Return transaction entity
```

**Note:** No balance updates in DB (blockchain is source of truth).

#### 3.3.4 GetEscrowBalance

**Purpose**: Query real-time balance from blockchain.

**Flow:**
```python
1. Get user from DB
2. Derive escrow PDA
3. Query Passeur: get_escrow_balance(escrow_pda)
   ↓ (Passeur → Solana RPC)
4. Return {escrow_account, balance, is_initialized}
```

**Performance:**
- Solana RPC query: ~50-200ms
- No caching (balance changes outside Pourtier)
- Fast enough for real-time UI updates

#### 3.3.5 CreateSubscription

**Purpose**: Create subscription with escrow balance validation.

**Flow:**
```python
1. Get plan details (price, duration)
2. Get user from DB
3. Check no active subscription exists
4. Derive escrow PDA
5. Query blockchain: escrow exists?
6. Query blockchain: get_escrow_balance(escrow_pda)
7. Verify balance >= plan price
8. Create Subscription entity (ACTIVE)
9. Save to PostgreSQL
10. Return subscription

# Note: Payment deduction happens later via cron job
# or immediately via ProcessSubscriptionBilling use case
```

---

## 4. Data Flow & Execution

### 4.1 Authentication Flow (Wallet-Based)
```
User clicks "Connect Wallet" in Frontend
    ↓
Frontend: wallet.connect() → Prompts user approval
    ↓
Frontend: wallet.signMessage("Lumiere Auth: {timestamp}")
    ↓
Frontend → POST /api/auth/verify
{
    "wallet_address": "ABC123...",
    "message": "Lumiere Auth: 2026-01-20T15:30:00Z",
    "signature": "XYZ789..."
}
    ↓
Pourtier.VerifyWalletSignature
    ↓
    SolanaWalletAdapter.verify_signature():
        1. Decode wallet public key (base58)
        2. Decode signature (base58)
        3. Verify Ed25519 signature
        4. Return True/False
    ↓
    UserRepository.get_by_wallet(wallet_address):
        1. Check L1 cache → MISS
        2. Check L2 (Redis) → MISS
        3. Query PostgreSQL → NULL
        4. Return None
    ↓
Response: {signature_valid: true, user_exists: false}
    ↓
Frontend shows "Create Account" form (legal docs)
User accepts Terms + Privacy Policy
    ↓
Frontend → POST /api/auth/create-account
{
    "wallet_address": "ABC123...",
    "signature": "XYZ789...",
    "message": "Lumiere Auth: 2026-01-20T15:30:00Z",
    "accepted_documents": ["uuid-terms", "uuid-privacy"],
    "wallet_type": "Phantom"
}
    ↓
Pourtier.CreateUserWithLegal
    ↓
    1. Verify signature again (security)
    2. Get active legal documents (2 docs)
    3. Verify all accepted (UUID match)
    4. Create User entity
       user = User(
           id=uuid4(),
           wallet_address="ABC123...",
           created_at=now
       )
    5. UserRepository.create(user)
       → PostgreSQL INSERT
       → Cache in L1 + L2
    6. For each accepted_document:
       acceptance = UserLegalAcceptance(
           user_id=user.id,
           document_id=doc_id,
           acceptance_method=WEB_CHECKBOX,
           ip_address=request.client.host,
           user_agent=request.headers["user-agent"]
       )
       → PostgreSQL INSERT
    7. Generate JWT token:
       jwt_handler.create_access_token(
           user_id=user.id,
           wallet_address="ABC123...",
           wallet_type="Phantom"
       )
       → Payload: {sub, wallet, wallet_type, exp, iat}
       → Sign with SECRET_KEY
    ↓
Response:
{
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "user_id": "uuid-user",
    "wallet_address": "ABC123..."
}
    ↓
Frontend stores JWT in localStorage
Frontend redirects to /dashboard
```

### 4.2 Escrow Initialization Flow (Prepare-Sign-Submit)
```
User clicks "Initialize Escrow" on dashboard
    ↓
Frontend → POST /api/escrow/prepare-initialize (with JWT)
Headers: {Authorization: "Bearer eyJhbG..."}
    ↓
AuthMiddleware.get_current_user():
    1. Extract JWT from Authorization header
    2. Decode JWT → {user_id, wallet_address}
    3. UserRepository.get_by_id(user_id)
       → Check L1 cache → HIT
       → Return User entity
    ↓
Pourtier.PrepareInitializeEscrow
    ↓
    1. Get user_id from current_user
    2. Derive escrow PDA:
       derive_escrow_pda(user.wallet_address, ESCROW_PROGRAM_ID)
       → Seeds: [b"escrow", user_wallet_bytes]
       → Pubkey.find_program_address(seeds, program_id)
       → Returns: ("EscrowPDA123...", bump=255)
    
    3. PasseurBridge.prepare_initialize_escrow(user.wallet_address)
       ↓
       POST passeur:9766/escrow/prepare-initialize
       {
           "userWallet": "ABC123...",
           "tokenMint": "USDC"
       }
       ↓
       Passeur builds unsigned transaction:
       - Instruction: escrow::initialize
       - Accounts: [user_wallet, escrow_pda, system_program, token_program]
       - Data: {bump, token_mint}
       ↓
       Passeur serializes transaction → base64
       ↓
       Response: {"transaction": "AQAAAAAAAAAAAQABAgM..."}
    ↓
Response:
{
    "transaction": "AQAAAAAAAAAAAQABAgM...",
    "token_mint": "USDC"
}
    ↓
Frontend receives unsigned transaction
Frontend shows confirmation dialog with details:
    "Initialize Escrow Account"
    "This will create your escrow account on Solana"
    "No funds will be transferred"
    "Gas fee: ~0.00001 SOL"
    ↓
User clicks "Approve"
    ↓
Frontend: wallet.signTransaction(base64_tx)
    ↓
Wallet (Phantom) shows transaction preview
User approves in wallet
Wallet signs transaction with private key
    ↓
Frontend receives signed transaction (base64)
    ↓
Frontend → POST /api/escrow/initialize
{
    "signed_transaction": "AQAAAAAAAAAAAQABAgM...[SIGNED]",
    "token_mint": "USDC"
}
    ↓
Pourtier.InitializeEscrow (IDEMPOTENT)
    ↓
    1. Generate idempotency key:
       key = f"initialize_escrow:{user_id}:USDC"
    
    2. Check RedisIdempotencyStore.get_async(key)
       → MISS (first attempt)
    
    3. Get user from DB
    
    4. Derive escrow PDA (same as prepare)
    
    5. PasseurBridge.submit_signed_transaction(signed_tx)
       ↓
       POST passeur:9766/transaction/submit
       {
           "signedTransaction": "AQAAAAAAAAAAAQABAgM...[SIGNED]"
       }
       ↓
       Passeur deserializes transaction
       Passeur verifies signatures
       Passeur submits to Solana RPC
       ↓
       Solana RPC processes transaction:
       - Verify user signature
       - Execute escrow::initialize instruction
       - Create escrow PDA account
       - Initialize balance = 0
       - Emit InitializeEscrow event
       ↓
       Transaction confirmed (~400ms finality)
       ↓
       Passeur waits for confirmation
       ↓
       Response: {"signature": "TxSig123..."}
    
    6. Create EscrowTransaction:
       tx = EscrowTransaction(
           id=uuid4(),
           user_id=user.id,
           tx_signature="TxSig123...",
           transaction_type=INITIALIZE,
           amount=0,
           token_mint="USDC",
           status=CONFIRMED,
           created_at=now,
           confirmed_at=now
       )
       → PostgreSQL INSERT
    
    7. Cache result in idempotency store (24h TTL)
    
    8. Return (user, "TxSig123...")
    ↓
Response:
{
    "escrow_account": "EscrowPDA123...",
    "balance": 0,
    "token_mint": "USDC",
    "tx_signature": "TxSig123..."
}
    ↓
Frontend updates UI:
    ✓ Escrow Initialized
    Balance: 0 USDC
    [Deposit Funds] button enabled
```

### 4.3 Deposit Flow (Prepare-Sign-Submit)
```
User clicks "Deposit" button
User enters amount: 100 USDC
    ↓
Frontend → POST /api/escrow/prepare-deposit (with JWT)
{
    "amount": 100
}
    ↓
Pourtier.PrepareDepositToEscrow
    ↓
    1. Get user_id from JWT
    2. Get user from DB (cached)
    3. Derive escrow PDA
    4. Check blockchain: escrow exists? (via Passeur query)
    5. Validate amount > 0
    
    6. PasseurBridge.prepare_deposit(user.wallet, escrow_pda, 100)
       ↓
       POST passeur:9766/escrow/prepare-deposit
       {
           "userWallet": "ABC123...",
           "escrowAccount": "EscrowPDA123...",
           "amount": 100
       }
       ↓
       Passeur builds unsigned transaction:
       - Instruction: token::transfer
       - From: user_wallet_token_account
       - To: escrow_pda_token_account
       - Amount: 100 * 10^6 (USDC has 6 decimals)
       ↓
       Response: {"transaction": "AQAAAAAAAAAAAQABAgM..."}
    ↓
Response:
{
    "transaction": "AQAAAAAAAAAAAQABAgM...",
    "escrow_account": "EscrowPDA123...",
    "amount": 100
}
    ↓
Frontend: wallet.signTransaction(base64_tx)
User approves 100 USDC transfer
    ↓
Frontend → POST /api/escrow/deposit
{
    "amount": 100,
    "signed_transaction": "AQAAAAAAAAAAAQABAgM...[SIGNED]"
}
    ↓
Pourtier.DepositToEscrow (IDEMPOTENT)
    ↓
    1. Idempotency key: f"deposit:{user_id}:100:{timestamp}"
    2. Check cache → MISS
    3. Get user, validate escrow exists
    4. Submit to Passeur
       ↓ Solana executes token::transfer
       ↓ Escrow balance: 0 → 100 USDC
    5. Check tx_signature not duplicate in DB
    6. Create EscrowTransaction (DEPOSIT, 100, CONFIRMED)
    7. Cache result (24h)
    8. Return transaction entity
    ↓
Response:
{
    "id": "uuid-tx",
    "tx_signature": "TxSig456...",
    "transaction_type": "deposit",
    "amount": 100,
    "status": "confirmed"
}
    ↓
Frontend queries balance (real-time):
    ↓
Frontend → GET /api/escrow/balance
    ↓
Pourtier.GetEscrowBalance
    ↓
    PasseurBridge.get_escrow_balance("EscrowPDA123...")
    ↓ Solana RPC query (~100ms)
    ↓ Returns: 100 USDC
    ↓
Response:
{
    "escrow_account": "EscrowPDA123...",
    "balance": 100,
    "is_initialized": true,
    "synced_from_blockchain": true
}
    ↓
Frontend updates UI:
    Balance: 100 USDC
```

### 4.4 Subscription Creation Flow
```
User navigates to /pricing
User clicks "Subscribe to Basic Plan" (10 USDC/month)
    ↓
Frontend → POST /api/subscriptions (with JWT)
{
    "plan_type": "basic"
}
    ↓
Pourtier.CreateSubscription
    ↓
    1. Get plan details:
       BASIC = {price: 10, duration_days: 30}
    
    2. Get user from JWT (cached)
    
    3. Check active subscription:
       SubscriptionRepository.get_active_by_user(user_id)
       → PostgreSQL: WHERE user_id=X AND status='ACTIVE'
       → Result: None (no active subscription)
    
    4. Derive escrow PDA
    
    5. Check blockchain: escrow exists?
       PasseurQueryService.check_escrow_exists(escrow_pda)
       ↓ Passeur → Solana RPC: getAccountInfo(escrow_pda)
       ↓ Result: Account exists, initialized
    
    6. Query blockchain balance:
       PasseurQueryService.get_escrow_balance(escrow_pda)
       ↓ Passeur → Solana RPC: getTokenAccountBalance(escrow_token_account)
       ↓ Result: 100 USDC
    
    7. Verify balance >= price:
       100 >= 10 ✓
    
    8. Calculate expiration:
       expires_at = now + timedelta(days=30)
    
    9. Create Subscription entity:
       subscription = Subscription(
           id=uuid4(),
           user_id=user.id,
           plan_type=BASIC,
           status=ACTIVE,
           started_at=now,
           expires_at=expires_at
       )
       → PostgreSQL INSERT
    
    10. Return subscription
    ↓
Response:
{
    "id": "uuid-sub",
    "user_id": "uuid-user",
    "plan_type": "basic",
    "status": "active",
    "started_at": "2026-01-20T15:30:00Z",
    "expires_at": "2026-02-19T15:30:00Z"
}
    ↓
Frontend updates UI:
    ✓ Basic Plan Active
    Expires: Feb 19, 2026
    [Manage Subscription]

Note: First payment (10 USDC) will be deducted later by:
- Billing cron job (runs daily, checks expiring subscriptions)
- OR ProcessSubscriptionBilling use case (immediate deduction)
```

---

## 5. Authentication & Authorization

### 5.1 Wallet-Based Authentication

**Flow:**
```
1. User connects wallet (Phantom/Backpack/Solflare)
2. Frontend generates message: "Lumiere Auth: {ISO_TIMESTAMP}"
3. User signs message in wallet (Ed25519 signature)
4. Frontend sends {wallet_address, message, signature} to Pourtier
5. Pourtier verifies signature with public key
6. Pourtier generates JWT token with {user_id, wallet_address, wallet_type}
7. Frontend stores JWT in localStorage
8. All subsequent requests include: Authorization: Bearer {JWT}
```

**Security Properties:**
- No passwords (wallet = identity)
- Signature proves wallet ownership
- Timestamp prevents replay attacks
- JWT expires after 24 hours (configurable)

### 5.2 JWT Token Structure

**Payload:**
```json
{
  "sub": "user-uuid",                    // User ID
  "wallet": "ABC123...",                 // Wallet address
  "wallet_type": "Phantom",              // Wallet application
  "iat": 1705766400,                     // Issued at (Unix timestamp)
  "exp": 1705852800,                     // Expires at (Unix timestamp)
  "type": "access"                       // Token type
}
```

**Encoding:**
```python
JWT = base64(header) + "." + base64(payload) + "." + HMAC-SHA256(secret, data)
```

**Validation:**
```python
1. Split token into [header, payload, signature]
2. Verify signature matches: HMAC-SHA256(SECRET_KEY, header + payload)
3. Check exp > now (not expired)
4. Extract user_id from sub
5. Load User from DB (with cache)
6. Return User entity
```

### 5.3 Authorization Middleware

**get_current_user Dependency:**
```python
@router.get("/api/users/profile")
async def get_profile(current_user: User = Depends(get_current_user)):
    # current_user is authenticated User entity
    return current_user.to_dict()
```

**Flow:**
```
Request → AuthMiddleware
    ↓
1. Extract Authorization header
2. Parse Bearer token
3. Decode JWT → {user_id, wallet_address}
4. Get User from DB (with L1+L2 cache)
5. Return User entity
    ↓
Endpoint receives authenticated User
```

**Error Responses:**
- Missing Authorization header → 401 Unauthorized
- Invalid JWT format → 401 Unauthorized
- Expired JWT → 401 Unauthorized
- User not found → 401 Unauthorized

---

## 6. Escrow Management

### 6.1 Escrow Architecture

**Key Principle:** Non-custodial - user always controls funds.

**Escrow Account Structure:**
```
Escrow PDA (Program Derived Address):
    Seeds: [b"escrow", user_wallet_pubkey]
    Owner: ESCROW_PROGRAM_ID
    
Account Data:
    - authority: user_wallet (can withdraw anytime)
    - balance: token_account.amount (USDC)
    - platform_authority: Option<Pubkey> (delegated)
    - trading_authority: Option<Pubkey> (delegated)
    - created_at: i64
    - bump: u8
```

**Delegation Model:**
```
User Wallet (Owner)
    │
    ├── Full Control: withdraw, delegate, revoke, close
    │
    ├─► Platform Authority (Optional Delegation)
    │   └── Can: deduct subscription fees
    │
    └─► Trading Authority (Optional Delegation)
        └── Can: execute trades (Chevalier)
```

### 6.2 Prepare-Sign-Submit Pattern

**Why?**
- Frontend never sends private keys to backend
- Backend never holds user funds
- User explicitly approves every transaction
- Blockchain cryptographically verifies ownership

**Pattern:**
```
1. PREPARE (Backend):
   - Backend builds unsigned transaction
   - Returns base64-encoded transaction to frontend
   
2. SIGN (Frontend/Wallet):
   - Frontend shows transaction details to user
   - User approves in wallet
   - Wallet signs transaction with private key
   - Frontend receives signed transaction
   
3. SUBMIT (Backend):
   - Frontend sends signed transaction to backend
   - Backend submits to blockchain via Passeur
   - Blockchain executes if signature valid
   - Backend records transaction in DB
```

**Example - Deposit:**
```python
# PREPARE
POST /api/escrow/prepare-deposit {"amount": 100}
→ Returns: {"transaction": "base64_unsigned_tx"}

# SIGN (Frontend)
signed_tx = await wallet.signTransaction(unsigned_tx)

# SUBMIT
POST /api/escrow/deposit {
    "amount": 100,
    "signed_transaction": "base64_signed_tx"
}
→ Returns: {"tx_signature": "TxSig123..."}
```

### 6.3 Balance Synchronization Strategy

**Decision:** No balance caching in Pourtier database.

**Rationale:**
- Solana finality: ~400ms (fast enough for real-time queries)
- Balance changes outside Pourtier (direct blockchain withdrawals)
- Cache invalidation complexity
- Single source of truth: blockchain

**Implementation:**
```python
async def get_escrow_balance(user_id: UUID) -> BalanceResponse:
    user = await user_repository.get_by_id(user_id)
    escrow_pda = derive_escrow_pda(user.wallet_address, PROGRAM_ID)
    
    # ALWAYS query blockchain (no cache)
    balance = await passeur_bridge.get_escrow_balance(escrow_pda)
    
    return BalanceResponse(
        escrow_account=escrow_pda,
        balance=balance,
        synced_from_blockchain=True,
        last_synced_at=datetime.now()
    )
```

**Performance:**
- Typical query: 100-200ms (Passeur → Solana RPC)
- Frontend debounces queries (max 1 per second)
- Acceptable for dashboard updates

### 6.4 Idempotency for Financial Operations

**Critical Requirement:** Prevent duplicate deposits/withdrawals.

**Implementation:**
```python
@dataclass
class IdempotencyKey:
    operation: str       # "deposit", "withdraw", "initialize"
    user_id: str
    params: dict         # {"amount": 100, "token": "USDC"}
    timestamp: str       # ISO format
    
    def to_redis_key(self) -> str:
        return f"idempotency:{self.operation}:{self.user_id}:{hash(params)}"
```

**Usage:**
```python
async def deposit_to_escrow(user_id, amount, signed_tx):
    # Generate idempotency key
    key = IdempotencyKey(
        operation="deposit",
        user_id=str(user_id),
        params={"amount": str(amount)},
        timestamp=datetime.now().isoformat()
    )
    
    # Check if already processed
    cached = await idempotency_store.get_async(key.to_redis_key())
    if cached:
        return cached  # Return previous result
    
    # Execute deposit
    result = await _execute_deposit(user_id, amount, signed_tx)
    
    # Store result for 24 hours
    await idempotency_store.set_async(
        key.to_redis_key(),
        result,
        ttl=86400
    )
    
    return result
```

**Edge Cases Handled:**
- Network retry → Same key returns cached result
- Browser refresh → Same key returns cached result
- Concurrent requests → First wins, second returns cached

---

## 7. Deployment Architecture

### 7.1 Docker Multi-Stage Build

**Dockerfile Structure:**
```dockerfile
# Stage 1: Base dependencies
FROM python:3.11-slim AS base
WORKDIR /app
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e .

# Stage 2: Development
FROM base AS development
ENV DEBUG=true
ENV ENV=development
COPY . .
EXPOSE 9000 9090 9091
CMD ["uvicorn", "pourtier.main:app", "--host", "0.0.0.0", "--port", "9000", "--reload"]

# Stage 3: Production
FROM base AS production
ENV DEBUG=false
ENV ENV=production
COPY . .
EXPOSE 8000 8090 8091
CMD ["uvicorn", "pourtier.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### 7.2 Port Allocation

| Environment | Main API | Metrics | Health | Usage |
|-------------|----------|---------|--------|-------|
| Development | 9000 | 9090 | 9091 | Local dev with reload |
| Production  | 8000 | 8090 | 8091 | Production deployment |
| Test        | 7000 | 7090 | 7091 | Integration tests |

### 7.3 Environment Configuration

**Development** (`.env.development`):
```bash
ENV=development
DEBUG=true
API_PORT=9000
API_RELOAD=true

DATABASE_URL=postgresql://pourtier_user:dev_pass@postgres:5432/pourtier_dev
REDIS_ENABLED=true
REDIS_HOST=lumiere-dev-redis
REDIS_DB=1

SOLANA_NETWORK=devnet
SOLANA_RPC_URL=https://api.devnet.solana.com

PASSEUR_URL=http://passeur:9766
COURIER_URL=http://courier:9765

LOG_LEVEL=DEBUG
LOG_FILE=null  # stdout for Docker

RATE_LIMIT_ENABLED=false
METRICS_ENABLED=true
```

**Production** (`.env.production`):
```bash
ENV=production
DEBUG=false
API_PORT=8000
API_RELOAD=false

DATABASE_URL=postgresql://pourtier_user:STRONG_PASS@postgres:5432/pourtier_db
REDIS_ENABLED=true
REDIS_HOST=redis
REDIS_DB=0

SOLANA_NETWORK=mainnet-beta
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com

PASSEUR_URL=http://passeur:8766
COURIER_URL=http://courier:8765

LOG_LEVEL=INFO
LOG_FILE=null

RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_SECOND=10
METRICS_ENABLED=true
```

### 7.4 Service Dependencies

**Startup Order:**
```
1. PostgreSQL (database)
2. Redis (cache, idempotency, rate limiting)
3. Passeur (blockchain bridge)
4. Courier (event bus)
5. Prophet, Architect, Chevalier, etc. (backend services)
6. Pourtier (API gateway - depends on all above)
7. Frontend (Next.js - depends on Pourtier)
```

**Health Checks:**
```bash
# Main API
curl http://localhost:9000/health

# Metrics endpoint
curl http://localhost:9090/metrics

# Dedicated health server
curl http://localhost:9091/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "components": {
    "database": {
      "status": "healthy",
      "pool": {"size": 5, "checked_out": 2}
    },
    "cache": {
      "status": "healthy",
      "enabled": true
    }
  },
  "monitoring": {
    "metrics_server": "http://0.0.0.0:9090/metrics",
    "health_server": "http://0.0.0.0:9091/health"
  }
}
```

---

## 8. API Reference

### 8.1 Authentication Endpoints

#### POST /api/auth/verify

Verify wallet signature without creating user.

**Request:**
```json
{
  "wallet_address": "ABC123...",
  "message": "Lumiere Auth: 2026-01-20T15:30:00Z",
  "signature": "XYZ789..."
}
```

**Response (200):**
```json
{
  "signature_valid": true,
  "user_exists": false,
  "user_id": null,
  "wallet_address": "ABC123..."
}
```

**Errors:**
- `401 Unauthorized`: Invalid signature

---

#### POST /api/auth/create-account

Create account with legal acceptance.

**Request:**
```json
{
  "wallet_address": "ABC123...",
  "signature": "XYZ789...",
  "message": "Lumiere Auth: 2026-01-20T15:30:00Z",
  "wallet_type": "Phantom",
  "accepted_documents": [
    "uuid-terms-v1",
    "uuid-privacy-v1"
  ],
  "ip_address": "192.168.1.1",
  "user_agent": "Mozilla/5.0..."
}
```

**Response (201):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user_id": "uuid-user",
  "wallet_address": "ABC123..."
}
```

**Errors:**
- `400 Bad Request`: User already exists or missing acceptances
- `401 Unauthorized`: Invalid signature

---

#### POST /api/auth/login

Login existing user.

**Request:**
```json
{
  "wallet_address": "ABC123...",
  "signature": "XYZ789...",
  "message": "Lumiere Auth: 2026-01-20T15:30:00Z",
  "wallet_type": "Phantom"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user_id": "uuid-user",
  "wallet_address": "ABC123...",
  "is_compliant": true,
  "pending_documents": []
}
```

**If not compliant:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "is_compliant": false,
  "pending_documents": [
    {
      "id": "uuid-privacy-v2",
      "document_type": "privacy_policy",
      "version": "2.0.0",
      "title": "Privacy Policy (Updated)"
    }
  ]
}
```

**Errors:**
- `404 Not Found`: User doesn't exist
- `401 Unauthorized`: Invalid signature

---

### 8.2 Escrow Endpoints

#### POST /api/escrow/prepare-initialize

Prepare unsigned initialize transaction.

**Headers:** `Authorization: Bearer {JWT}`

**Response (200):**
```json
{
  "transaction": "AQAAAAAAAAAAAQABAgM...",
  "token_mint": "USDC"
}
```

---

#### POST /api/escrow/initialize

Submit signed initialize transaction.

**Headers:** `Authorization: Bearer {JWT}`

**Request:**
```json
{
  "signed_transaction": "AQAAAAAAAAAAAQABAgM...[SIGNED]",
  "token_mint": "USDC"
}
```

**Response (201):**
```json
{
  "escrow_account": "EscrowPDA123...",
  "balance": 0,
  "token_mint": "USDC",
  "tx_signature": "TxSig123..."
}
```

**Errors:**
- `409 Conflict`: Escrow already initialized
- `503 Service Unavailable`: Blockchain error

---

#### POST /api/escrow/prepare-deposit

Prepare unsigned deposit transaction.

**Headers:** `Authorization: Bearer {JWT}`

**Request:**
```json
{
  "amount": 100
}
```

**Response (200):**
```json
{
  "transaction": "AQAAAAAAAAAAAQABAgM...",
  "escrow_account": "EscrowPDA123...",
  "amount": 100
}
```

---

#### POST /api/escrow/deposit

Submit signed deposit transaction.

**Headers:** `Authorization: Bearer {JWT}`

**Request:**
```json
{
  "amount": 100,
  "signed_transaction": "AQAAAAAAAAAAAQABAgM...[SIGNED]"
}
```

**Response (201):**
```json
{
  "id": "uuid-tx",
  "user_id": "uuid-user",
  "tx_signature": "TxSig456...",
  "transaction_type": "deposit",
  "amount": 100,
  "token_mint": "USDC",
  "status": "confirmed",
  "created_at": "2026-01-20T15:30:00Z",
  "confirmed_at": "2026-01-20T15:30:01Z"
}
```

---

#### GET /api/escrow/balance

Get real-time balance from blockchain.

**Headers:** `Authorization: Bearer {JWT}`

**Response (200):**
```json
{
  "escrow_account": "EscrowPDA123...",
  "balance": 100,
  "token_mint": "USDC",
  "is_initialized": true,
  "initialized_at": null,
  "synced_from_blockchain": true,
  "last_synced_at": "2026-01-20T15:30:00Z"
}
```

**If not initialized:**
```json
{
  "escrow_account": null,
  "balance": 0,
  "token_mint": "USDC",
  "is_initialized": false,
  "synced_from_blockchain": true,
  "last_synced_at": "2026-01-20T15:30:00Z"
}
```

---

#### GET /api/escrow/transactions

List escrow transactions.

**Headers:** `Authorization: Bearer {JWT}`

**Query Parameters:**
- `transaction_type` (optional): Filter by type (deposit, withdraw, initialize)

**Response (200):**
```json
{
  "transactions": [
    {
      "id": "uuid-tx-1",
      "tx_signature": "TxSig123...",
      "transaction_type": "initialize",
      "amount": 0,
      "status": "confirmed",
      "created_at": "2026-01-19T10:00:00Z"
    },
    {
      "id": "uuid-tx-2",
      "tx_signature": "TxSig456...",
      "transaction_type": "deposit",
      "amount": 100,
      "status": "confirmed",
      "created_at": "2026-01-20T15:30:00Z"
    }
  ],
  "total": 2
}
```

---

### 8.3 Subscription Endpoints

#### POST /api/subscriptions

Create new subscription.

**Headers:** `Authorization: Bearer {JWT}`

**Request:**
```json
{
  "plan_type": "basic"
}
```

**Response (201):**
```json
{
  "id": "uuid-sub",
  "user_id": "uuid-user",
  "plan_type": "basic",
  "status": "active",
  "started_at": "2026-01-20T15:30:00Z",
  "expires_at": "2026-02-19T15:30:00Z",
  "created_at": "2026-01-20T15:30:00Z",
  "updated_at": "2026-01-20T15:30:00Z"
}
```

**Errors:**
- `400 Bad Request`: User already has active subscription or insufficient funds
- `500 Internal Server Error`: Subscription creation failed

---

#### GET /api/subscriptions

Get user subscriptions.

**Headers:** `Authorization: Bearer {JWT}`

**Response (200):**
```json
[
  {
    "id": "uuid-sub",
    "plan_type": "basic",
    "status": "active",
    "expires_at": "2026-02-19T15:30:00Z"
  }
]
```

---

#### GET /api/subscriptions/check

Check subscription status.

**Headers:** `Authorization: Bearer {JWT}`

**Response (200):**
```json
{
  "has_active_subscription": true,
  "current_plan": "basic"
}
```

---

### 8.4 Wallet Endpoints

#### GET /api/wallet/balance

Get wallet USDC balance (not escrow).

**Query Parameters:**
- `wallet` (required): Solana wallet address

**Response (200):**
```json
{
  "wallet_address": "ABC123...",
  "balance": "500.50",
  "token_mint": "USDC"
}
```

---

## 9. Database Schema

### 9.1 Users Table
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    wallet_address VARCHAR(44) UNIQUE NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    CONSTRAINT valid_wallet_length CHECK (LENGTH(wallet_address) >= 32)
);

CREATE INDEX idx_users_wallet ON users(wallet_address);
CREATE INDEX idx_users_created_at ON users(created_at DESC);
```

**Important:** NO escrow fields stored in users table.

---

### 9.2 Subscriptions Table
```sql
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    plan_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL,
    started_at TIMESTAMP NOT NULL,
    expires_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    CONSTRAINT valid_plan CHECK (plan_type IN ('free', 'basic', 'pro')),
    CONSTRAINT valid_status CHECK (status IN ('active', 'cancelled', 'expired')),
    CONSTRAINT expires_after_start CHECK (
        expires_at IS NULL OR expires_at > started_at
    )
);

CREATE INDEX idx_subscriptions_user ON subscriptions(user_id);
CREATE INDEX idx_subscriptions_status ON subscriptions(status);
CREATE INDEX idx_subscriptions_user_status ON subscriptions(user_id, status);
```

---

### 9.3 Escrow Transactions Table
```sql
CREATE TABLE escrow_transactions (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tx_signature VARCHAR(88) UNIQUE NOT NULL,
    transaction_type VARCHAR(50) NOT NULL,
    amount DECIMAL(20, 8) NOT NULL,
    token_mint VARCHAR(44) NOT NULL,
    status VARCHAR(50) NOT NULL,
    subscription_id UUID,
    confirmed_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    CONSTRAINT valid_transaction_type CHECK (
        transaction_type IN ('deposit', 'withdraw', 'initialize')
    ),
    CONSTRAINT valid_tx_status CHECK (
        status IN ('pending', 'confirmed', 'failed')
    )
);

CREATE INDEX idx_escrow_transactions_user ON escrow_transactions(user_id);
CREATE INDEX idx_escrow_transactions_type ON escrow_transactions(transaction_type);
CREATE INDEX idx_escrow_transactions_created_at 
    ON escrow_transactions(created_at DESC);
```

---

### 9.4 Legal Documents Table
```sql
CREATE TABLE legal_documents (
    id UUID PRIMARY KEY,
    document_type VARCHAR(50) NOT NULL,
    version VARCHAR(20) NOT NULL,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    status VARCHAR(20) NOT NULL,
    effective_date TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    CONSTRAINT valid_document_type CHECK (
        document_type IN ('terms_of_service', 'privacy_policy')
    ),
    CONSTRAINT valid_document_status CHECK (
        status IN ('draft', 'active', 'archived')
    )
);

CREATE INDEX idx_legal_documents_type ON legal_documents(document_type);
CREATE INDEX idx_legal_documents_type_status 
    ON legal_documents(document_type, status);
```

---

### 9.5 User Legal Acceptances Table
```sql
CREATE TABLE user_legal_acceptances (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    document_id UUID NOT NULL REFERENCES legal_documents(id) ON DELETE RESTRICT,
    accepted_at TIMESTAMP NOT NULL DEFAULT NOW(),
    acceptance_method VARCHAR(30) NOT NULL,
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    CONSTRAINT valid_acceptance_method CHECK (
        acceptance_method IN ('web_checkbox', 'api_explicit', 'migration_implicit')
    ),
    CONSTRAINT unique_user_document UNIQUE (user_id, document_id)
);

CREATE INDEX idx_user_legal_acceptances_user ON user_legal_acceptances(user_id);
CREATE INDEX idx_user_legal_acceptances_document 
    ON user_legal_acceptances(document_id);
```

---

## 10. Integration Points

### 10.1 Passeur Bridge Service

**Purpose**: Blockchain transaction execution and balance queries

**Endpoints Used:**
```
POST /escrow/prepare-initialize
POST /escrow/prepare-deposit
POST /escrow/prepare-withdraw
POST /transaction/submit
GET  /escrow/balance/{escrow_account}
GET  /escrow/{escrow_account}
GET  /wallet/balance?wallet={address}
```

**Resilience:**
- Circuit Breaker: Opens after 5 failures, closes after 2 successes
- Retry: 3 attempts with exponential backoff (1s → 2s → 4s)
- Timeout: 30s total, 10s connect

---

### 10.2 Courier Event Bus

**Purpose**: Real-time event broadcasting

**Events Published:**
```
user.created              → User registration complete
escrow.initialized        → Escrow account created
escrow.deposit.completed  → Funds deposited
subscription.created      → Subscription activated
subscription.expired      → Subscription expired
```

**Usage:**
```python
await courier_client.publish(
    channel="user.events",
    event_type="user.created",
    data={"user_id": str(user.id), "wallet": wallet}
)
```

---

### 10.3 Backend Microservices (Proxy Routes)

Pourtier acts as API Gateway and proxies requests to backend services:

| Route | Target Service | Purpose |
|-------|----------------|---------|
| `/api/prophet/*` | Prophet:9081 | AI strategy generation |
| `/api/architect/*` | Architect:9082 | Strategy repository |
| `/api/chevalier/*` | Chevalier:9084 | Trade execution |
| `/api/cartographe/*` | Cartographe:9083 | Backtesting |
| `/api/chronicler/*` | Chronicler:9085 | Market data |
| `/api/tsdl/*` | TSDL:9086 | Strategy compilation |

**Example Proxy:**
```python
@router.post("/api/prophet/generate")
async def generate_strategy(
    request: dict,
    current_user: User = Depends(get_current_user)
):
    # Add user_id to request
    request["user_id"] = str(current_user.id)
    
    # Proxy to Prophet
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.PROPHET_URL}/generate",
            json=request,
            timeout=60.0
        )
    
    return response.json()
```

---

## 11. Monitoring & Observability

### 11.1 Prometheus Metrics

**Metrics Exported:**
```
# Request metrics
pourtier_requests_total{method, endpoint, status}
pourtier_request_duration_seconds{method, endpoint}

# Passeur Bridge metrics
passeur_requests_total{operation, status}
passeur_request_duration_seconds{operation}
passeur_circuit_breaker_state_changes_total{state}

# Database metrics
database_connection_pool_size
database_connection_pool_checked_out
database_query_duration_seconds{operation}

# Cache metrics
cache_hits_total{layer}  # L1 or L2
cache_misses_total{layer}
cache_size{layer}
```

**Prometheus Scrape Config:**
```yaml
scrape_configs:
  - job_name: 'pourtier'
    static_configs:
      - targets: ['pourtier:9090']
    scrape_interval: 15s
```

### 11.2 Health Checks

**Dedicated Health Server (Port 9091):**
```bash
curl http://localhost:9091/health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "components": {
    "database": {
      "status": "healthy",
      "pool": {
        "size": 5,
        "checked_out": 2,
        "overflow": 0,
        "checked_in": 3
      }
    },
    "cache": {
      "status": "healthy",
      "enabled": true,
      "info": "connected"
    }
  },
  "timestamp": "2026-01-20T15:30:00Z"
}
```

### 11.3 Logging

**Structured Logging (JSON in production):**
```json
{
  "timestamp": "2026-01-20T15:30:00.123Z",
  "level": "INFO",
  "logger": "pourtier.application.use_cases.deposit_to_escrow",
  "request_id": "req-abc123",
  "user_id": "uuid-user",
  "message": "Deposit completed",
  "tx_signature": "TxSig456...",
  "amount": 100,
  "duration_ms": 250
}
```

**Log Levels:**
- `DEBUG`: Request/response details, cache hits/misses
- `INFO`: User actions, transactions, state changes
- `WARNING`: Retries, circuit breaker state changes
- `ERROR`: Failed operations, validation errors
- `CRITICAL`: Database connection loss, Passeur unavailable

---

## 12. Troubleshooting Guide

### 12.1 Common Issues

#### Issue: "401 Unauthorized" on authenticated endpoints

**Symptoms:**
```
POST /api/escrow/balance
Response: 401 Unauthorized
```

**Diagnosis:**
```bash
# Check JWT token
curl -X POST http://localhost:9000/api/auth/verify \
  -H "Content-Type: application/json" \
  -d '{
    "wallet_address": "ABC123...",
    "message": "Lumiere Auth: 2026-01-20T15:30:00Z",
    "signature": "XYZ789..."
  }'

# Check token expiration
echo "eyJhbGciOiJIUzI1NiIs..." | base64 -d
```

**Common Causes:**
1. JWT expired (24 hours default)
2. Invalid signature (wallet changed)
3. User deleted from database

**Solution:**
```bash
# Re-authenticate
POST /api/auth/login
{
  "wallet_address": "ABC123...",
  "signature": "new_signature",
  "message": "new_message"
}
```

---

#### Issue: "409 Conflict - Escrow already initialized"

**Symptoms:**
```
POST /api/escrow/initialize
Response: 409 Conflict
```

**Diagnosis:**
```bash
# Check blockchain state
curl http://localhost:9000/api/escrow/balance \
  -H "Authorization: Bearer {JWT}"

# Check transactions
curl http://localhost:9000/api/escrow/transactions \
  -H "Authorization: Bearer {JWT}"
```

**Solution:**
- User already has escrow → Skip initialization
- Frontend should check `is_initialized` before showing init button

---

#### Issue: "400 Bad Request - Insufficient escrow balance"

**Symptoms:**
```
POST /api/subscriptions
{"plan_type": "basic"}
Response: 400 Bad Request - Insufficient escrow balance
```

**Diagnosis:**
```bash
# Check balance
GET /api/escrow/balance
Response: {"balance": 5, "is_initialized": true}

# Plan requires 10 USDC for Basic
```

**Solution:**
```bash
# Deposit more funds
POST /api/escrow/prepare-deposit {"amount": 10}
# Sign transaction in wallet
POST /api/escrow/deposit {
  "amount": 10,
  "signed_transaction": "..."
}
```

---

#### Issue: Circuit Breaker OPEN for Passeur

**Symptoms:**
```
Logs: "Passeur Bridge circuit breaker is OPEN for initialize_escrow"
```

**Diagnosis:**
```bash
# Check Passeur health
curl http://localhost:9766/health

# Check Prometheus metrics
curl http://localhost:9090/metrics | grep passeur_circuit
```

**Common Causes:**
1. Passeur service down
2. Solana RPC unavailable
3. Network issues

**Solution:**
```bash
# Restart Passeur
docker restart lumiere-dev-passeur

# Wait for circuit to close (60s timeout)
# Or restart Pourtier to reset circuit
docker restart lumiere-dev-pourtier
```

---

#### Issue: Database connection pool exhausted

**Symptoms:**
```
Logs: "TimeoutError: QueuePool limit of 5 exceeded"
```

**Diagnosis:**
```bash
# Check health endpoint
curl http://localhost:9091/health

# Look at pool stats
{
  "database": {
    "pool": {
      "size": 5,
      "checked_out": 5,  # All connections in use
      "overflow": 0
    }
  }
}
```

**Solution:**
```bash
# Increase pool size in settings
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=5

# Restart Pourtier
docker restart lumiere-dev-pourtier
```

---

### 12.2 Performance Issues

#### Issue: Slow balance queries (>1s)

**Diagnosis:**
```bash
# Profile request
time curl http://localhost:9000/api/escrow/balance \
  -H "Authorization: Bearer {JWT}"

# Check Passeur latency
curl http://localhost:9766/health
```

**Common Causes:**
1. Solana RPC slow (public endpoint)
2. Network latency to Passeur
3. Passeur overloaded

**Solution:**
```bash
# Use private RPC endpoint
SOLANA_RPC_URL=https://your-private-rpc.com

# Or add caching (with TTL)
# Note: Balance can change outside Pourtier, so cache carefully
```

---

#### Issue: High rate limit rejections

**Symptoms:**
```
Response: 429 Too Many Requests
```

**Diagnosis:**
```bash
# Check Redis rate limit keys
docker exec lumiere-dev-redis redis-cli KEYS "rate_limit:*"

# Check metrics
curl http://localhost:9090/metrics | grep rate_limit
```

**Solution:**
```bash
# Increase rate limit
RATE_LIMIT_REQUESTS_PER_SECOND=20
RATE_LIMIT_BURST_SIZE=40

# Or disable for development
RATE_LIMIT_ENABLED=false
```

---

### 12.3 Data Verification

**Check User:**
```sql
SELECT id, wallet_address, created_at 
FROM users 
WHERE wallet_address = 'ABC123...';
```

**Check Subscriptions:**
```sql
SELECT id, plan_type, status, expires_at 
FROM subscriptions 
WHERE user_id = 'uuid-user' 
ORDER BY created_at DESC;
```

**Check Transactions:**
```sql
SELECT tx_signature, transaction_type, amount, status, created_at 
FROM escrow_transactions 
WHERE user_id = 'uuid-user' 
ORDER BY created_at DESC 
LIMIT 10;
```

**Check Legal Compliance:**
```sql
SELECT u.wallet_address, 
       COUNT(DISTINCT ula.document_id) as accepted_docs,
       (SELECT COUNT(*) FROM legal_documents WHERE status = 'active') as active_docs
FROM users u
LEFT JOIN user_legal_acceptances ula ON u.id = ula.user_id
WHERE u.id = 'uuid-user'
GROUP BY u.id, u.wallet_address;
```

---

**END OF DOCUMENT**

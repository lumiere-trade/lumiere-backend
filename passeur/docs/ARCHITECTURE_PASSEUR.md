# Passeur - Solana Blockchain Bridge

**Version:** 0.1.0
**Last Updated:** January 20, 2026
**Component Type:** Hybrid Python/Node.js Blockchain Bridge with Resilience Patterns

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [System Architecture](#2-system-architecture)
3. [Core Components](#3-core-components)
4. [Data Flow & Transaction Lifecycle](#4-data-flow--transaction-lifecycle)
5. [Resilience Patterns](#5-resilience-patterns)
6. [Deployment Architecture](#6-deployment-architecture)
7. [API Reference](#7-api-reference)
8. [Integration Points](#8-integration-points)
9. [Monitoring & Observability](#9-monitoring--observability)
10. [Troubleshooting Guide](#10-troubleshooting-guide)

---

## 1. Executive Summary

### 1.1 Purpose

Passeur is Lumière's **blockchain bridge service** that provides a clean abstraction layer between Python backend services and Solana blockchain smart contracts. It handles transaction preparation, signing coordination, escrow management, and blockchain state queries with enterprise-grade resilience patterns.

### 1.2 Key Capabilities

- **User-Based Escrow Management**: Non-custodial escrow accounts (one per user)
- **Two-Layer Architecture**: Python FastAPI proxy + Node.js bridge for optimal performance
- **Transaction Preparation**: Unsigned transaction generation for client-side signing
- **Authority Delegation**: Platform (subscription fees) and Trading (Chevalier) authority management
- **Resilience Patterns**: Circuit breakers, retry logic, idempotency guarantees, rate limiting
- **Comprehensive API**: REST endpoints mirroring Anchor smart contract instructions

### 1.3 Architecture Decision

**Why Two Layers?**

Python FastAPI (external port 8766/9766):
- Resilience proxy with circuit breakers
- Redis-backed idempotency (7-day TTL for financial operations)
- Authentication and rate limiting
- Integration with Lumière Python ecosystem

Node.js Bridge (internal port 8768/9768):
- Native @solana/web3.js integration
- Faster transaction building
- Anchor IDL-based instruction generation
- WebSocket support for real-time events

### 1.4 Technology Stack

- **Python Layer**: FastAPI, aiohttp, Redis, Pydantic
- **Node.js Bridge**: Express, WebSocket, @solana/web3.js, @solana/spl-token
- **Blockchain**: Solana (devnet/mainnet-beta), Anchor framework
- **Infrastructure**: Docker multi-stage builds, supervisord orchestration
- **Dependencies**: shared==0.6.0 (resilience patterns, health checks)

---

## 2. System Architecture

### 2.1 High-Level Architecture
```
┌─────────────────────────────────────────────────────────────┐
│              Frontend (Next.js) - app.lumiere.trade         │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTPS/REST
┌────────────────────▼────────────────────────────────────────┐
│            Pourtier (API Gateway) - Port 8000/9000          │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                 Passeur (This Component)                    │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │    Python FastAPI (External API) - Port 8766/9766    │  │
│  │                                                       │  │
│  │  Resilience Features:                                │  │
│  │  - Circuit Breaker (5 failures → open)               │  │
│  │  - Retry with Exponential Backoff                    │  │
│  │  - Redis Idempotency Store (7-day TTL)               │  │
│  │  - Rate Limiting (10 RPC/s, burst 20)                │  │
│  │  - Request/Response Validation                       │  │
│  │                                                       │  │
│  │  API Endpoints:                                       │  │
│  │  - POST /escrow/prepare-* (8 endpoints)              │  │
│  │  - POST /transaction/submit                          │  │
│  │  - GET  /escrow/{address}, /balance/{account}        │  │
│  │  - GET  /transaction/status/{signature}              │  │
│  │  - GET  /wallet/balance                              │  │
│  └───────────────────┬──────────────────────────────────┘  │
│                      │ Internal HTTP (localhost only)      │
│  ┌───────────────────▼──────────────────────────────────┐  │
│  │   Node.js Bridge (Internal) - Port 8768/9768         │  │
│  │                                                       │  │
│  │  Blockchain Operations:                              │  │
│  │  - Transaction Building (@solana/web3.js)            │  │
│  │  - PDA Derivation (["escrow", user_pubkey])          │  │
│  │  - Instruction Assembly (Anchor discriminators)      │  │
│  │  - Account Deserialization                           │  │
│  │  - WebSocket Events                                  │  │
│  └───────────────────┬──────────────────────────────────┘  │
└──────────────────────┼──────────────────────────────────────┘
                       │ HTTPS
              ┌────────▼─────────┐
              │   Solana RPC     │
              │  (devnet/mainnet)│
              └────────┬─────────┘
                       │
              ┌────────▼─────────┐
              │ Escrow Program   │
              │ (Anchor Smart    │
              │  Contract)       │
              └──────────────────┘

External Dependencies:
┌──────────┐  ┌───────────┐  ┌────────────┐
│  Redis   │  │Prometheus │  │   Health   │
│(Idempot.)│  │(Metrics)  │  │   Server   │
│Port: 6379│  │Port: 9792 │  │ Port: 9793 │
└──────────┘  └───────────┘  └────────────┘
```

### 2.2 Component Interactions

**Transaction Preparation Flow:**
```
Frontend (User clicks "Deposit") → Pourtier → Passeur FastAPI
    ↓
1. Check Redis: idempotency_key = "escrow:deposit:{account}:{amount}"
   - If duplicate → return cached unsigned transaction (201 OK)
   - If new → proceed
    ↓
2. Call Node.js Bridge (internal HTTP)
    ↓
Node.js Bridge:
3. Derive PDA: ["escrow", user_pubkey] → escrow_address
4. Get associated token accounts
5. Build instruction with Anchor discriminator
6. Create unsigned Transaction
7. Serialize to base64
    ↓
8. Return to Python → Store in Redis (7-day TTL)
9. Return to Frontend: {transaction: "base64...", amount: "..."}
    ↓
Frontend signs with Phantom/Solflare
    ↓
POST /transaction/submit → Bridge submits to Solana
```

---

## 3. Core Components

### 3.1 Python FastAPI Layer

#### 3.1.1 Configuration (config/settings.py)

**Hybrid YAML + ENV Architecture:**

Priority: `ENV variables > environment-specific YAML > default YAML > Pydantic defaults`
```python
class PasseurConfig(BaseSettings):
    # External API (Python FastAPI)
    api_host: str = "0.0.0.0"
    api_port: int = 8766  # 8766 prod, 9766 dev
    
    # Internal Bridge (Node.js)
    bridge_host: str = "127.0.0.1"
    bridge_port: int = 8768  # 8768 prod, 9768 dev
    
    # Solana Blockchain
    solana_rpc_url: Optional[str]  # From ENV (required)
    solana_network: str = "devnet"  # devnet, testnet, mainnet-beta
    program_id: str = "9gvUtaF..."  # Escrow program
    platform_keypair_path: Optional[str]  # From ENV (required)
    
    # Resilience Configuration
    resilience: ResilienceConfig
        circuit_breakers:
            solana_rpc: {failure_threshold: 5, timeout: 30.0}
            bridge_server: {failure_threshold: 3, timeout: 60.0}
        retry:
            transaction_submission: {max_attempts: 3, backoff: 2.0}
            rpc_query: {max_attempts: 5, backoff: 2.0}
        timeouts:
            rpc_call: 10.0
            transaction_confirmation: 30.0
            bridge_call: 15.0
        rate_limiting:
            rpc_calls_per_second: 10.0
            burst_size: 20
        idempotency:
            financial_operations: 7  # days
            security_operations: 3   # days
            query_operations: 1      # days
    
    # Health & Metrics
    health: {port: 9793, check_interval: 30}
    metrics: {port: 9792, enabled: True}
    
    # Redis
    redis: {host: "localhost", port: 6379, db: 0}
```

**Configuration Files:**
- `config/default.yaml` - Base configuration
- `config/development.yaml` - Development overrides (port 9766, debug logging)
- `config/production.yaml` - Production settings (port 8766, info logging)
- `config/test.yaml` - Testing configuration

#### 3.1.2 BridgeClient (infrastructure/blockchain/bridge_client.py)

**Purpose**: HTTP client for Node.js bridge with resilience patterns.
```python
class BridgeClient:
    """
    Client for Node.js bridge server.
    
    Features:
    - Circuit breaker (prevent cascading failures)
    - Retry with exponential backoff + jitter
    - Timeout protection (15s default)
    """
    
    def __init__(self):
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=3,  # Open after 3 failures
            success_threshold=2,  # Close after 2 successes
            timeout=60.0,         # Stay open for 60s
        )
        
        self.retry = Retry(
            max_attempts=3,
            initial_delay=2.0,
            max_delay=10.0,
            backoff_multiplier=2.0,
            jitter=True,
        )
    
    async def prepare_initialize(
        self, user_wallet: str, max_balance: Optional[int] = None
    ) -> Dict[str, Any]:
        """Prepare initialize escrow transaction."""
        return await self._call_bridge(
            "/escrow/prepare-initialize",
            method="POST",
            data={"userWallet": user_wallet, "maxBalance": max_balance},
        )
    
    # 10+ other methods mirroring Node.js endpoints
```

#### 3.1.3 RedisIdempotencyStore (infrastructure/cache/)

**Purpose**: Exactly-once semantics for financial operations.
```python
class RedisIdempotencyStore:
    """
    Redis-backed idempotency store.
    
    Key Format: idempotency:{operation}:{params}
    TTL: 7 days (financial), 3 days (security), 1 day (queries)
    """
    
    async def check_and_store(
        self, key: str, ttl: int
    ) -> Tuple[bool, Optional[Any]]:
        """
        Atomic check-and-reserve operation.
        
        Returns:
            (is_duplicate, cached_result)
        """
        cached = await self.get_async(key)
        if cached:
            return (True, cached)  # Duplicate request
        
        await self.set_async(key, {}, ttl)  # Reserve key
        return (False, None)  # First request
```

#### 3.1.4 API Routes (presentation/api/routes/escrow.py)

**Idempotency-First Design Pattern:**
```python
@router.post("/escrow/prepare-initialize")
async def prepare_initialize(request: PrepareInitializeRequest, req: Request):
    """
    Prepare initialize escrow transaction.
    
    Idempotency: 7 days (financial operation)
    """
    bridge_client = req.app.state.bridge_client
    redis_store = req.app.state.redis_store
    
    # Generate idempotency key
    key = f"escrow:init:{request.userWallet}"
    ttl = 7 * 86400  # 7 days
    
    # Check for duplicate
    is_duplicate, cached = await redis_store.check_and_store(key, ttl)
    
    if is_duplicate and cached:
        return PrepareInitializeResponse(**cached)  # Return cached
    
    # Call bridge (first request)
    result = await bridge_client.prepare_initialize(
        user_wallet=request.userWallet,
        max_balance=request.maxBalance,
    )
    
    # Store result
    await redis_store.store_result(key, result)
    
    return PrepareInitializeResponse(**result)
```

### 3.2 Node.js Bridge Server

#### 3.2.1 Bridge Server (bridge/server.js)

**Purpose**: Direct Solana blockchain integration.

**Why Node.js?**
- Native @solana/web3.js support
- Better performance for transaction building
- Simpler Anchor IDL integration
- Smaller attack surface (isolated process)

**Key Implementation:**
```javascript
// Configuration (hybrid YAML + ENV, same as Python)
const CONFIG = loadConfig();

// Platform keypair for subscription fee withdrawals
const platformKeypair = Keypair.fromSecretKey(...);

// Solana connection
const connection = new Connection(CONFIG.solana_rpc_url, 'confirmed');
const programId = new PublicKey(CONFIG.program_id);

// Express endpoints mirror Python API
app.post('/escrow/prepare-initialize', async (req, res) => {
  const { userWallet, maxBalance } = req.body;
  
  // Derive PDA (user-only, no strategy_id)
  const [escrowPDA, bump] = PublicKey.findProgramAddressSync(
    [Buffer.from('escrow'), userPubkey.toBuffer()],
    programId
  );
  
  // Build instruction with Anchor discriminator
  const ix = buildInitializeEscrowInstruction({...});
  
  // Create unsigned transaction
  const { blockhash } = await connection.getLatestBlockhash();
  const transaction = new Transaction();
  transaction.recentBlockhash = blockhash;
  transaction.feePayer = userPubkey;
  transaction.add(ix);
  
  // Serialize unsigned (for client signing)
  const serialized = transaction.serialize({
    requireAllSignatures: false,
  });
  
  res.json({
    success: true,
    transaction: serialized.toString('base64'),
    escrowAccount: escrowPDA.toString(),
    bump,
  });
});
```

#### 3.2.2 Instruction Builders (bridge/instructions/)

**Discriminators (discriminators.js):**

Auto-generated from Anchor IDL:
```javascript
const DISCRIMINATORS = {
  INITIALIZE: Buffer.from([243, 160, 77, 153, 11, 92, 48, 209]),
  DEPOSIT: Buffer.from([11, 156, 96, 218, 39, 163, 180, 19]),
  DELEGATE_PLATFORM_AUTHORITY: Buffer.from([126, 172, 138, 174, 184, 236, 63, 169]),
  DELEGATE_TRADING_AUTHORITY: Buffer.from([164, 159, 115, 90, 166, 214, 57, 95]),
  REVOKE_PLATFORM_AUTHORITY: Buffer.from([7, 7, 103, 233, 134, 154, 157, 153]),
  REVOKE_TRADING_AUTHORITY: Buffer.from([207, 57, 250, 223, 186, 166, 244, 101]),
  WITHDRAW: Buffer.from([136, 235, 181, 5, 101, 109, 57, 81]),
  CLOSE: Buffer.from([139, 171, 94, 146, 191, 91, 144, 50]),
};
```

**Account Deserialization:**
```javascript
async function fetchEscrowAccount(escrowAddress) {
  const accountInfo = await connection.getAccountInfo(escrowAddress);
  const data = accountInfo.data;
  let offset = 8; // Skip discriminator
  
  const user = new PublicKey(data.slice(offset, offset + 32));
  offset += 32;
  const platformAuthority = new PublicKey(data.slice(offset, offset + 32));
  offset += 32;
  const tradingAuthority = new PublicKey(data.slice(offset, offset + 32));
  offset += 32;
  const tokenMint = new PublicKey(data.slice(offset, offset + 32));
  offset += 32;
  const bump = data[offset];
  offset += 1;
  const flags = data[offset];
  offset += 1;
  
  return {
    user,
    platformAuthority,
    tradingAuthority,
    tokenMint,
    bump,
    isPlatformActive: (flags & 0b0001) !== 0,
    isTradingActive: (flags & 0b0010) !== 0,
    isPaused: (flags & 0b0100) !== 0,
  };
}
```

---

## 4. Data Flow & Transaction Lifecycle

### 4.1 Initialize Escrow (Complete Flow)
```
User clicks "Initialize Escrow" → Frontend → Pourtier

POST /passeur/escrow/prepare-initialize
{
  "userWallet": "7xKXtg...",
  "maxBalance": null
}

↓ Passeur FastAPI

Step 1: Generate Idempotency Key
key = "escrow:init:7xKXtg..."
ttl = 604800  # 7 days

Step 2: Check Redis
is_duplicate, cached = await redis.check_and_store(key, ttl)
If duplicate → return cached (END)

Step 3: Call Node.js Bridge
POST http://127.0.0.1:9768/escrow/prepare-initialize

↓ Node.js Bridge

Step 4: Derive PDA
seeds = [b"escrow", user_pubkey]
[escrowPDA, bump] = findProgramAddress(seeds, programId)

Step 5: Get Associated Token Accounts
tokenMint = "4zMMC..." (USDC devnet)
escrowTokenAccount = getAssociatedTokenAddress(tokenMint, escrowPDA, true)

Step 6: Build Instruction
data = [DISCRIMINATOR, bump, maxBalance]
keys = [escrow, escrowTokenAccount, tokenMint, user, SystemProgram, ...]

Step 7: Create Unsigned Transaction
transaction = new Transaction()
transaction.add(instruction)
serialized = transaction.serialize({requireAllSignatures: false})

Step 8: Return to Python
{
  "success": true,
  "transaction": "base64...",
  "escrowAccount": "8vN...",
  "bump": 255
}

Step 9: Store in Redis
await redis.store_result(key, result)

Step 10: Return to Frontend
Response 201: {transaction, escrowAccount, bump}

↓ Frontend

Step 11: User Signs with Wallet (Phantom/Solflare)

Step 12: Submit Signed Transaction
POST /passeur/transaction/submit
{signedTransaction: "base64..."}

↓ Node.js Bridge

Step 13: Submit to Solana RPC
signature = await connection.sendRawTransaction(tx)

Step 14: Return Signature
{success: true, signature: "5abc..."}
```

---

## 5. Resilience Patterns

### 5.1 Circuit Breaker

**Purpose**: Prevent cascading failures when Solana RPC or bridge is down.

**Configuration:**
```yaml
circuit_breakers:
  solana_rpc:
    failure_threshold: 5     # Open after 5 failures
    success_threshold: 3     # Close after 3 successes
    timeout: 30.0            # Stay open for 30s
  bridge_server:
    failure_threshold: 3
    success_threshold: 2
    timeout: 60.0
```

**States:**
- **CLOSED**: Normal operation (all requests pass through)
- **OPEN**: Circuit is open (all requests fail fast)
- **HALF_OPEN**: Testing if service recovered (limited requests)

### 5.2 Retry with Exponential Backoff

**Configuration:**
```yaml
retry:
  transaction_submission:
    max_attempts: 3
    initial_delay: 2.0
    max_delay: 10.0
    backoff_multiplier: 2.0
    jitter: true
```

**Retry Schedule:**
- Attempt 1: 0s
- Attempt 2: 2s + jitter
- Attempt 3: 4s + jitter
- Attempt 4: 8s + jitter (capped at max_delay)

### 5.3 Idempotency Guarantees

**Critical Operations Protected:**

| Operation | Key Format | TTL | Purpose |
|-----------|-----------|-----|---------|
| Initialize Escrow | `escrow:init:{wallet}` | 7 days | Prevent duplicate escrow accounts |
| Deposit | `escrow:deposit:{account}:{amount}` | 7 days | Prevent double deposits |
| Withdraw | `escrow:withdraw:{account}:{amount}` | 7 days | Prevent double withdrawals |
| Delegate Authority | `escrow:delegate-platform:{account}` | 3 days | Prevent duplicate delegation |

**Flow:**
```python
# 1. Check if request is duplicate
is_duplicate, cached = await redis.check_and_store(key, ttl)

if is_duplicate:
    return cached  # Return previous result immediately

# 2. Execute operation (first time)
result = await bridge.prepare_initialize(...)

# 3. Store result for future duplicate requests
await redis.store_result(key, result)

return result
```

### 5.4 Rate Limiting

**Configuration:**
```yaml
rate_limiting:
  rpc_calls_per_second: 10.0
  burst_size: 20
```

**Token Bucket Algorithm:**
- Steady rate: 10 requests/second
- Burst allowance: 20 requests
- Per-user rate limiting (by wallet address)

---

## 6. Deployment Architecture

### 6.1 Docker Multi-Stage Build
```dockerfile
# Stage 1: Node.js dependencies
FROM node:18-alpine AS node-builder
WORKDIR /app/bridge
COPY passeur/bridge/package*.json ./
RUN npm ci
COPY passeur/bridge/ ./

# Stage 2: Python dependencies
FROM python:3.12-slim AS python-builder
WORKDIR /build
RUN apt-get update && apt-get install -y gcc g++
COPY passeur/pyproject.toml ./
COPY passeur/src/ ./src/
RUN pip install --no-cache-dir .

# Stage 3: Development
FROM python:3.12-slim AS development
WORKDIR /app
# Install Node.js + supervisord
RUN apt-get install -y nodejs supervisor
# Copy from builders
COPY --from=python-builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=node-builder /app/bridge ./bridge
COPY passeur/supervisord.conf /etc/supervisor/conf.d/passeur.conf
EXPOSE 9766
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/passeur.conf"]
```

### 6.2 Supervisord Orchestration
```ini
[supervisord]
nodaemon=true
logfile=/dev/null

[program:bridge]
command=node server.js
directory=/app/bridge
autostart=true
autorestart=true
environment=NODE_ENV="development"

[program:api]
command=python3 -m passeur.main
directory=/app
autostart=true
autorestart=true
priority=10
environment=PYTHONUNBUFFERED="1"
```

### 6.3 Port Allocation

| Environment | Python API | Node.js Bridge | Health | Metrics |
|-------------|-----------|----------------|---------|---------|
| Production  | 8766      | 8768           | 8793    | 8792    |
| Development | 9766      | 9768           | 9793    | 9792    |
| Test        | 7766      | 7768           | 7793    | 7792    |

---

## 7. API Reference

### 7.1 Escrow Operations

#### POST /escrow/prepare-initialize

**Request:**
```json
{
  "userWallet": "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU",
  "maxBalance": null
}
```

**Response (200):**
```json
{
  "success": true,
  "transaction": "base64-encoded-unsigned-tx",
  "escrowAccount": "8vNxJtfa3fVAjKPBP4zymvRwUqR4fgLdvT8r1pGvQZMC",
  "bump": 255,
  "message": "Transaction ready for signing"
}
```

#### POST /escrow/prepare-deposit

**Request:**
```json
{
  "userWallet": "7xKXtg...",
  "escrowAccount": "8vNxJt...",
  "amount": 100.0
}
```

**Response (200):**
```json
{
  "success": true,
  "transaction": "base64...",
  "amount": "100000000",
  "message": "Transaction ready for signing"
}
```

#### GET /escrow/{address}

**Response (200):**
```json
{
  "success": true,
  "data": {
    "address": "8vNxJt...",
    "user": "7xKXtg...",
    "platformAuthority": "11111111111111111111111111111111",
    "tradingAuthority": "11111111111111111111111111111111",
    "tokenMint": "4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU",
    "bump": 255,
    "isPlatformActive": false,
    "isTradingActive": false,
    "isPaused": false,
    "totalDeposited": "1000000",
    "totalWithdrawn": "0"
  }
}
```

---

## 8. Integration Points

### 8.1 Pourtier (API Gateway)

**Usage**: Routes authenticated requests to Passeur.
```
POST https://api.lumiere.trade/passeur/escrow/prepare-initialize
Authorization: Bearer <jwt>
```

### 8.2 Frontend (Next.js)

**Usage**: Wallet integration and transaction signing.
```typescript
// 1. Prepare transaction
const response = await fetch('/passeur/escrow/prepare-deposit', {
  method: 'POST',
  body: JSON.stringify({userWallet, escrowAccount, amount}),
});
const {transaction} = await response.json();

// 2. Sign with wallet
const signed = await wallet.signTransaction(
  Transaction.from(Buffer.from(transaction, 'base64'))
);

// 3. Submit
await fetch('/passeur/transaction/submit', {
  method: 'POST',
  body: JSON.stringify({
    signedTransaction: Buffer.from(signed.serialize()).toString('base64'),
  }),
});
```

### 8.3 Chevalier (Trade Execution)

**Usage**: Execute trades using delegated trading authority.

Future integration for live trading.

---

## 9. Monitoring & Observability

### 9.1 Health Checks

**Kubernetes-Compatible Probes:**
```bash
# Liveness (is service alive?)
GET /health/live
Response: {"status": "healthy", "alive": true}

# Readiness (can accept traffic?)
GET /health/ready
Response: {"status": "healthy", "ready": true}

# Overall health
GET /health
Response: {
  "status": "healthy",
  "service": "passeur",
  "version": "0.1.0"
}
```

### 9.2 Metrics (Prometheus)

**Exposed on port 9792:**
```
# Circuit breaker state
passeur_circuit_breaker_state{service="bridge_server"} 0

# Transaction metrics
passeur_transactions_total{operation="initialize"} 42
passeur_transaction_errors_total{operation="deposit"} 3

# Latency
passeur_request_duration_seconds{endpoint="/escrow/prepare-deposit"} 0.12
```

### 9.3 Logging

**Log Levels:**
- **DEBUG**: Full request/response traces
- **INFO**: Transaction submissions, escrow operations
- **WARNING**: Circuit breaker state changes, retry attempts
- **ERROR**: Transaction failures, bridge connection errors
- **CRITICAL**: System-wide failures

---

## 10. Troubleshooting Guide

### 10.1 Bridge Connection Failed

**Symptoms:**
```
ERROR: Bridge connection failed
Status: 502 Bad Gateway
```

**Diagnosis:**
```bash
# Check Node.js bridge status
curl http://localhost:9768/health

# Check supervisord
docker exec passeur supervisorctl status

# Check logs
docker logs passeur | grep bridge
```

**Solution:**
```bash
# Restart bridge via supervisord
docker exec passeur supervisorctl restart bridge

# Or restart entire container
docker restart passeur
```

### 10.2 Idempotency Key Collision

**Symptoms:**
```
WARNING: Duplicate request detected
Returning cached transaction
```

**This is expected behavior!** Idempotency is working correctly.

**To clear cache (testing only):**
```bash
docker exec lumiere-dev-redis redis-cli DEL "idempotency:escrow:init:7xKXtg..."
```

### 10.3 Transaction Timeout

**Symptoms:**
```
ERROR: Transaction confirmation timeout
Signature: 5abc...
```

**Diagnosis:**
```bash
# Check transaction on Solana
solana confirm 5abc... --url devnet

# Check RPC health
curl https://api.devnet.solana.com -X POST \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"getHealth"}'
```

**Solutions:**
- Transaction may still confirm (check explorer)
- Retry with increased confirmation timeout
- Switch to different RPC endpoint

---

**END OF DOCUMENT**

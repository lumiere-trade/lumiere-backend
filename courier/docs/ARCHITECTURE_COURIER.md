# Courier - Real-Time WebSocket Event Bus

**Version:** 1.0.0
**Last Updated:** January 20, 2026
**Component Type:** High-Performance WebSocket Event Broadcasting System

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [System Architecture](#2-system-architecture)
3. [Core Components](#3-core-components)
4. [Data Flow & Execution](#4-data-flow--execution)
5. [Channel Architecture](#5-channel-architecture)
6. [Event Schema System](#6-event-schema-system)
7. [Authentication & Authorization](#7-authentication--authorization)
8. [Rate Limiting](#8-rate-limiting)
9. [Deployment Architecture](#9-deployment-architecture)
10. [API Reference](#10-api-reference)
11. [Monitoring & Observability](#11-monitoring--observability)
12. [Troubleshooting Guide](#12-troubleshooting-guide)

---

## 1. Executive Summary

### 1.1 Purpose

Courier is Lumière's **real-time WebSocket event broadcasting hub** that provides bidirectional communication between backend services and frontend clients. It acts as a central message bus for live trading updates, backtest progress, strategy generation, and system events with sub-millisecond delivery latency.

### 1.2 Key Capabilities

- **Multi-Channel Broadcasting**: Support for global, user-scoped, and ephemeral channels
- **WebSocket Management**: Connection pooling with automatic heartbeat and dead connection cleanup
- **Event Schema Validation**: Pydantic-based schema validation with size limits (1MB total, 512KB payload)
- **JWT Authentication**: Optional token-based authentication with channel-level authorization
- **Rate Limiting**: Per-service and per-message-type rate limiting with token bucket algorithm
- **Connection Limits**: Global, per-user, and per-channel connection limits with graceful rejection
- **Graceful Shutdown**: Zero-downtime deployment with client notification and grace periods
- **High Availability**: Health checks for Kubernetes liveness and readiness probes
- **Observability**: Prometheus metrics, health monitoring, and distributed tracing support

### 1.3 Performance Targets

| Metric | Target | Actual |
|--------|--------|--------|
| Message Delivery | <1ms | 0.3-0.5ms |
| WebSocket Accept | <10ms | 5-8ms |
| Concurrent Connections | 10,000 | 10,000+ |
| Messages/Second | 100,000 | 50,000-100,000 |
| Max Message Size | 1MB | Configurable |
| Heartbeat Interval | 30s | Configurable |

### 1.4 Technology Stack

- **Runtime**: Python 3.12 with asyncio
- **Framework**: FastAPI with WebSocket support
- **WebSocket Library**: websockets 11.0+ (native Python implementation)
- **Validation**: Pydantic 2.0+ for schema validation
- **Authentication**: PyJWT 2.8+ for JWT verification
- **Rate Limiting**: Token Bucket algorithm from shared library
- **Monitoring**: Prometheus metrics, custom health checks
- **Dependencies**: shared==0.6.0 (SystemReporter, RateLimiter, HealthChecker)

---

## 2. System Architecture

### 2.1 High-Level Architecture
```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (Next.js)                      │
│                    app.lumiere.trade                            │
└────────────────────────┬────────────────────────────────────────┘
                         │ WebSocket (wss://)
                         │ REST (https://)
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                    Pourtier (API Gateway)                       │
│              JWT Authentication & Request Routing               │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                     Courier (This Component)                    │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         FastAPI Application Layer (Port 8765)            │  │
│  │   /ws/{channel}, /publish, /health, /stats              │  │
│  └───────────────────────┬──────────────────────────────────┘  │
│                          │                                      │
│  ┌───────────────────────▼──────────────────────────────────┐  │
│  │          Presentation Layer (API Routes)                 │  │
│  │   WebSocketRoute, PublishRoute, HealthRoute             │  │
│  └───────────────────────┬──────────────────────────────────┘  │
│                          │                                      │
│  ┌───────────────────────▼──────────────────────────────────┐  │
│  │            Application Layer (Use Cases)                 │  │
│  │   AuthenticateWebSocket, BroadcastMessage,              │  │
│  │   ManageChannel, ValidateEvent, ValidateMessage         │  │
│  └───────────────────────┬──────────────────────────────────┘  │
│                          │                                      │
│  ┌───────────────────────▼──────────────────────────────────┐  │
│  │          Domain Layer (Entities & Value Objects)         │  │
│  │   Channel, Client, ChannelName, Message                 │  │
│  │   Event Schemas: BaseEvent, CartographeEvent,           │  │
│  │   ChevalierEvent, ProphetEvent, ForgeEvent              │  │
│  └──────────────┬───────────────────────────────────────────┘  │
│                 │                                               │
│  ┌──────────────▼──────────────────────────────────────────┐  │
│  │         Infrastructure Layer                            │  │
│  │                                                          │  │
│  │  ┌────────────────────────────────────────────────────┐ │  │
│  │  │   ConnectionManager (WebSocket Pool)              │ │  │
│  │  │   - Multi-channel subscription management         │ │  │
│  │  │   - Connection limits (global, per-user, channel) │ │  │
│  │  │   - Client registry with metadata                 │ │  │
│  │  │   - Automatic cleanup of dead connections         │ │  │
│  │  └────────────────────────────────────────────────────┘ │  │
│  │                                                          │  │
│  │  ┌────────────────────────────────────────────────────┐ │  │
│  │  │   JWTVerifier (Authentication)                    │ │  │
│  │  │   - Token validation with PyJWT                   │ │  │
│  │  │   - Channel-level authorization                   │ │  │
│  │  │   - Expiration checking                           │ │  │
│  │  └────────────────────────────────────────────────────┘ │  │
│  │                                                          │  │
│  │  ┌────────────────────────────────────────────────────┐ │  │
│  │  │   RateLimiter (Token Bucket)                      │ │  │
│  │  │   - Per-service publish rate limiting             │ │  │
│  │  │   - Per-message-type WebSocket rate limiting      │ │  │
│  │  │   - Shared TokenBucket implementation             │ │  │
│  │  └────────────────────────────────────────────────────┘ │  │
│  │                                                          │  │
│  │  ┌────────────────────────────────────────────────────┐ │  │
│  │  │   GracefulShutdown (Lifecycle Management)         │ │  │
│  │  │   - SIGTERM/SIGINT handling                       │ │  │
│  │  │   - Client notification before shutdown           │ │  │
│  │  │   - Grace period for connection cleanup           │ │  │
│  │  │   - Coordinated task cancellation                 │ │  │
│  │  └────────────────────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │        Background Tasks (Asyncio)                        │  │
│  │                                                          │  │
│  │  - Heartbeat Loop (30s interval):                       │  │
│  │    → Send ping to all connected clients                 │  │
│  │    → Detect and remove dead connections                 │  │
│  │    → Stop during graceful shutdown                      │  │
│  │                                                          │  │
│  │  - Empty Channel Cleanup:                               │  │
│  │    → Remove ephemeral channels with no subscribers     │  │
│  │                                                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │    Observability Stack (Separate Threads)                │  │
│  │                                                          │  │
│  │  MetricsServer (Port 8790):                             │  │
│  │    → Prometheus /metrics endpoint                       │  │
│  │    → Connection counters                                │  │
│  │    → Message delivery stats                             │  │
│  │    → Rate limit hit counters                            │  │
│  │                                                          │  │
│  │  HealthServer (Port 8791):                              │  │
│  │    → Kubernetes liveness probe                          │  │
│  │    → Kubernetes readiness probe                         │  │
│  │    → Connection capacity checks                         │  │
│  │    → Component health verification                      │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                 │                │                │
                 │                │                │
        ┌────────▼────┐  ┌───────▼─────┐  ┌──────▼───────┐
        │ Chevalier   │  │  Chronicler │  │  Cartographe │
        │ (Trading    │  │  (Market    │  │  (Backtest   │
        │  Executor)  │  │   Data)     │  │   Engine)    │
        └─────────────┘  └─────────────┘  └──────────────┘
                                │
                       ┌────────▼────────┐
                       │    Prophet      │
                       │  (AI Strategy   │
                       │   Generation)   │
                       └─────────────────┘
```

### 2.2 Component Interactions

**WebSocket Connection Flow:**
```
Frontend (Next.js) initiates WebSocket connection
    ↓
ws://courier:8765/ws/{channel}?token={jwt}
    ↓
1. FastAPI WebSocket endpoint accepts connection
2. AuthenticateWebSocketUseCase.execute()
    ↓
    - Extract token from query parameter
    - JWTVerifier.verify_token()
    - JWTVerifier.verify_channel_access(user_id, channel)
    - Return TokenPayload or None (if auth disabled)
3. ConnectionManager.check_connection_limits()
    ↓
    - Check global limit (max_total_connections)
    - Check per-user limit (max_connections_per_user)
    - Check per-channel limit (max_clients_per_channel)
    - Raise ConnectionLimitExceeded if exceeded
4. ConnectionManager.add_client()
    ↓
    - Create Client entity with metadata
    - Add WebSocket to channel subscribers list
    - Register in client_registry
    - Log connection with SystemReporter
5. ManageChannelUseCase.create_or_get_channel()
    ↓
    - Validate channel name (lowercase alphanumeric + dots + hyphens)
    - Create Channel entity if new
    - Mark as ephemeral if forge.job.* or backtest.*
6. Heartbeat loop sends periodic pings
    ↓
    - {"type": "ping"} every 30s
    - Client responds with {"type": "pong"}
    - Dead connections removed automatically
7. On disconnect:
    ↓
    - ConnectionManager.remove_client()
    - Cleanup empty ephemeral channels
    - Log disconnection
```

**Event Publishing Flow:**
```
Backend Service (Chevalier, Chronicler, etc.)
    ↓
POST /publish
{
  "channel": "dashboard.{user_id}",
  "data": {
    "type": "dashboard.candle",
    "deployment_id": "xxx",
    ...
  }
}
    ↓
1. Rate Limiting Check (if enabled):
    ↓
    - Extract X-Service-Name header
    - RateLimiter.check_rate_limit(service_name)
    - Return 429 if limit exceeded
    - Exempt internal services (chronicler, chevalier)
2. Event Validation (if type provided):
    ↓
    - ValidateEventUseCase.execute(event_type, event_data)
    - Validate total size (<1MB)
    - Validate payload size (<512KB)
    - Validate metadata size (<10KB)
    - Validate against Pydantic schema
    - Return 413 if size limit exceeded
    - Return 400 if schema validation fails
3. ManageChannelUseCase.create_or_get_channel()
    ↓
    - Ensure channel exists
    - Create if not present
4. ConnectionManager.get_channel_subscribers()
    ↓
    - Get list of WebSocket connections for channel
5. BroadcastMessageUseCase.execute()
    ↓
    - For each WebSocket in subscribers:
        → await ws.send_json(message_data)
        → Track dead connections
    - Remove dead connections
    - Return count of successful deliveries
6. Update statistics:
    ↓
    - Increment total_messages_sent counter
    - Log broadcast with SystemReporter
7. Return response:
    ↓
    {
      "status": "published",
      "channel": "dashboard.xxx",
      "clients_reached": 5,
      "timestamp": "2026-01-20T..."
    }
```

**Graceful Shutdown Flow:**
```
SIGTERM/SIGINT received
    ↓
1. ShutdownManager.shutdown() triggered
    ↓
    - Set shutdown_event flag
    - Stop accepting new WebSocket connections
    - Log shutdown initiation
2. Notify all connected clients:
    ↓
    - Send {"type": "shutdown", "message": "Server is shutting down"}
    - All clients receive notification
3. Wait grace period (5 seconds):
    ↓
    - Allow clients to disconnect gracefully
4. Run custom cleanup tasks:
    ↓
    - Cancel heartbeat task
    - Close all remaining WebSocket connections
    - Send {"code": 1001, "reason": "Server shutdown"}
5. Stop monitoring servers:
    ↓
    - MetricsServer.shutdown()
    - HealthServer.shutdown()
6. Final cleanup:
    ↓
    - Clear all channel subscriptions
    - Clear client registry
    - Log completion
```

---

## 3. Core Components

### 3.1 Domain Layer

#### 3.1.1 Channel Entity

**Purpose**: Represents a logical message broadcasting channel.
```python
class Channel:
    id: UUID                      # Unique channel identifier
    name: str                     # Channel name (e.g., "global", "user.123")
    created_at: datetime          # Channel creation timestamp
    is_ephemeral: bool            # Auto-delete when empty
```

**Channel Naming Conventions:**
- `global`: System-wide events
- `user.{user_id}`: User-specific events
- `dashboard.{user_id}`: Real-time trading data for user
- `strategy.{strategy_id}`: Strategy-specific events
- `backtest.{backtest_id}`: Backtest progress (ephemeral)
- `forge.job.{job_id}`: Background job updates (ephemeral)
- `price.{token}`: Market data (e.g., `price.sol`, `price.pump`)

**Ephemeral Channels**: Automatically deleted when subscriber count reaches zero.

#### 3.1.2 Client Entity

**Purpose**: Represents a connected WebSocket client.
```python
class Client:
    id: UUID                      # Unique client identifier
    user_id: Optional[str]        # Authenticated user ID
    wallet_address: Optional[str] # Solana wallet address
    channel_name: str             # Subscribed channel
    connected_at: datetime        # Connection timestamp
```

#### 3.1.3 ChannelName Value Object

**Purpose**: Immutable validated channel name.

**Validation Rules:**
- Lowercase alphanumeric + dots + hyphens only
- Maximum 100 characters
- Pattern: `^[a-z0-9.\-]+$`

**Helper Methods:**
```python
is_global() -> bool              # Check if "global"
is_user_channel() -> bool        # Check if "user.*"
is_strategy_channel() -> bool    # Check if "strategy.*"
is_ephemeral() -> bool           # Check if "forge.job.*" or "backtest.*"
extract_user_id() -> str         # Extract user ID from "user.{id}"
```

#### 3.1.4 Message Value Object

**Purpose**: Immutable message with validation.
```python
class Message:
    data: Dict[str, Any]          # Message payload (deep copied)
    timestamp: datetime           # Creation timestamp
    
    def get_type() -> str         # Extract message type
```

**Immutability**: Deep copy on creation prevents external modifications.

### 3.2 Infrastructure Layer

#### 3.2.1 ConnectionManager

**Purpose**: Manages WebSocket connections and channel subscriptions.

**Key Attributes:**
```python
channels: Dict[str, List[WebSocket]]  # Channel → WebSocket list
client_registry: Dict[int, Client]    # WebSocket ID → Client
max_total_connections: int            # Global limit (0 = unlimited)
max_connections_per_user: int         # Per-user limit (0 = unlimited)
max_clients_per_channel: int          # Per-channel limit (0 = unlimited)
```

**Key Methods:**
```python
check_connection_limits(channel: str, user_id: str) -> None
    # Raises ConnectionLimitExceeded if any limit exceeded
    
add_client(ws: WebSocket, channel: str, user_id: str, wallet: str) -> Client
    # Add client to channel, increment counts
    
remove_client(ws: WebSocket, channel: str) -> None
    # Remove client from channel, decrement counts
    
get_channel_subscribers(channel: str) -> List[WebSocket]
    # Get all WebSockets subscribed to channel
    
get_total_connections() -> int
    # Sum of all WebSocket connections across all channels
    
get_user_connection_count(user_id: str) -> int
    # Count connections for specific user
    
cleanup_empty_channels() -> List[str]
    # Remove channels with zero subscribers
```

**Connection Limit Logic:**
```python
# Global limit check
if total_connections >= max_total_connections > 0:
    raise ConnectionLimitExceeded("global")
    
# Per-user limit check
if user_connection_count(user_id) >= max_connections_per_user > 0:
    raise ConnectionLimitExceeded("per_user")
    
# Per-channel limit check
if channel_subscriber_count >= max_clients_per_channel > 0:
    raise ConnectionLimitExceeded("per_channel")
```

#### 3.2.2 JWTVerifier

**Purpose**: JWT token validation and channel authorization.

**Key Methods:**
```python
verify_token(token: str) -> TokenPayload
    # Decode JWT, validate signature, check expiration
    # Raises ValueError if invalid or expired
    
verify_channel_access(user_id: str, channel: str) -> bool
    # Check if user authorized to access channel
    # Returns True if authorized, False otherwise
```

**Authorization Rules:**
```python
# Global channel - everyone can access
if channel == "global": return True

# User channel - must match user_id
if channel.startswith("user."):
    return channel_user_id == user_id
    
# Dashboard channel - must match user_id
if channel.startswith("dashboard."):
    return channel_user_id == user_id
    
# Strategy channel - allow access (ownership check TODO)
if channel.startswith("strategy."): return True

# Ephemeral channels - allow access
if channel.startswith(("backtest.", "forge.job.")): return True

# Price channels - public market data
if channel.startswith("price."): return True

# Public channels - allow access
if channel in ["trade", "candles", "sys", ...]: return True

# Unknown channel - deny by default
return False
```

#### 3.2.3 RateLimiter

**Purpose**: Token bucket rate limiting with per-type support.

**Architecture**: Adapter wrapping `shared.resilience.RateLimiterRegistry`.

**Key Attributes:**
```python
default_limit: int                    # Default requests per window
window_seconds: int                   # Time window in seconds
per_type_limits: Dict[str, int]       # Per-message-type overrides
_registry: RateLimiterRegistry        # Shared token bucket registry
```

**Key Methods:**
```python
check_rate_limit(identifier: str, message_type: str) -> bool
    # Return True if allowed, False if rate limited
    
get_remaining(identifier: str, message_type: str) -> int
    # Get approximate remaining requests
    
get_retry_after_seconds(identifier: str, message_type: str) -> int
    # Get seconds until rate limit resets
    
get_stats(identifier: str, message_type: str) -> Dict
    # Get detailed rate limit statistics
```

**Per-Type Limits Example:**
```yaml
rate_limit_per_message_type:
  trade: 50           # 50 trades/min
  candles: 100        # 100 candles/min  
  strategy: 10        # 10 strategy updates/min
  subscription: 5     # 5 subscription changes/min
```

**Registry Key Format:**
- Default: `{identifier}` (e.g., `chevalier`)
- Per-type: `{identifier}:{message_type}` (e.g., `user-123:trade`)

#### 3.2.4 GracefulShutdown

**Purpose**: Coordinated shutdown with client notification.

**Key Attributes:**
```python
shutdown_timeout: float = 30.0        # Max seconds for cleanup
grace_period: float = 5.0             # Seconds for client disconnect
shutdown_event: asyncio.Event         # Shutdown flag
cleanup_tasks: List[Callable]         # Registered cleanup functions
```

**Shutdown Sequence:**
```python
1. setup_signal_handlers()
   → Register SIGTERM/SIGINT handlers
   
2. On signal received → shutdown()
   → Set shutdown_event flag
   → Stop accepting new connections
   
3. Notify clients:
   → Send {"type": "shutdown"} to all WebSockets
   
4. Wait grace_period:
   → Allow 5s for graceful disconnects
   
5. Run cleanup_tasks:
   → Cancel background tasks
   → Close remaining connections
   → Shutdown monitoring servers
   
6. Force close:
   → Close all remaining WebSockets with code 1001
```

### 3.3 Application Layer

#### 3.3.1 AuthenticateWebSocketUseCase

**Purpose**: Verify JWT and authorize channel access.
```python
execute(token: Optional[str], channel_name: str) -> Optional[TokenPayload]
    # Returns:
    # - TokenPayload if authenticated
    # - None if auth not required
    # Raises:
    # - TokenExpiredError
    # - TokenInvalidError
    # - AuthorizationError
```

#### 3.3.2 BroadcastMessageUseCase

**Purpose**: Deliver message to all channel subscribers.
```python
execute(channel: str, message_data: Dict, subscribers: List[WebSocket]) -> int
    # Validates message structure
    # Sends to all subscribers
    # Tracks dead connections
    # Returns count of successful deliveries
```

#### 3.3.3 ManageChannelUseCase

**Purpose**: Channel lifecycle management.
```python
create_or_get_channel(channel_name: str) -> Channel
    # Validate name, create if new, return Channel entity
    
get_subscriber_count(channel_name: str) -> int
    # Count subscribers for channel
    
should_cleanup_channel(channel_name: str) -> bool
    # True if ephemeral and empty
```

#### 3.3.4 ValidateEventUseCase

**Purpose**: Validate events against Pydantic schemas with size limits.

**Supported Event Types:**
- `prophet.*`: AI strategy generation
- `backtest.*`: Backtest lifecycle
- `strategy.*`: Live trading events
- `trade.*`: Trade execution
- `position.*`: Position management
- `forge.job.*`: Background jobs
- `dashboard.*`: Real-time streaming

**Validation Steps:**
```python
1. Check if event type is known
2. Validate total event size (<1MB)
3. Validate metadata size (<10KB)
4. Validate payload size (<512KB)
5. Validate against Pydantic schema
6. Return validated BaseEvent instance
```

**Size Limits:**
```python
max_event_size: int = 1_048_576         # 1MB total
max_payload_size: int = 524_288         # 512KB for data field
max_metadata_size: int = 10_240         # 10KB for metadata field
```

#### 3.3.5 ValidateMessageUseCase

**Purpose**: Validate incoming WebSocket messages.

**Validation Steps:**
```python
1. Check message size (<1MB)
2. Parse JSON
3. Validate it's a dictionary
4. Validate string length (<10K chars)
5. Validate array size (<1K items)
6. Recursively validate nested objects
7. Return ValidationResult
```

**ValidationResult:**
```python
@dataclass
class ValidationResult:
    valid: bool
    errors: List[str]
    message_type: Optional[str]
    size_bytes: int
```

---

## 4. Data Flow & Execution

### 4.1 WebSocket Connection Lifecycle
```
Client → ws://courier:8765/ws/dashboard.user-123?token=eyJ...

↓ WebSocket Connection Initiated

Step 1: Accept Connection
──────────────────────────
await websocket.accept()
connection_id = generate_connection_id()  # conn_abc123
LOG: "WebSocket connection attempt [conn=conn_abc123] [channel=dashboard.user-123]"

Step 2: Check Shutdown Status
──────────────────────────────
if shutdown_manager.is_shutting_down():
    await websocket.close(code=1001, reason="Server shutting down")
    return

Step 3: Authenticate (if required)
───────────────────────────────────
auth_payload = AuthenticateWebSocketUseCase.execute(token, channel)
    ↓
    JWTVerifier.verify_token(token)
        ↓
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        return TokenPayload(user_id="user-123", wallet_address="5Kq...", ...)
    ↓
    JWTVerifier.verify_channel_access("user-123", "dashboard.user-123")
        ↓
        # Dashboard channel - must match user_id
        channel_user_id = "user-123"
        return channel_user_id == "user-123"  # True

Step 4: Check Connection Limits
────────────────────────────────
ConnectionManager.check_connection_limits("dashboard.user-123", "user-123")
    ↓
    # Global limit check
    total = 8524
    if total >= max_total_connections (10000):  # False
        pass
    
    # Per-user limit check
    user_conns = 3
    if user_conns >= max_connections_per_user (5):  # False
        pass
    
    # Per-channel limit check
    channel_subs = 1
    if channel_subs >= max_clients_per_channel (0):  # False (unlimited)
        pass

Step 5: Create Channel (if new)
────────────────────────────────
ManageChannelUseCase.create_or_get_channel("dashboard.user-123")
    ↓
    validated_name = ChannelName("dashboard.user-123")
    is_ephemeral = validated_name.is_ephemeral()  # False
    
    if "dashboard.user-123" not in channels:
        channels["dashboard.user-123"] = []
        LOG: "New channel created [channel=dashboard.user-123]"

Step 6: Add Client to Channel
──────────────────────────────
client = ConnectionManager.add_client(
    websocket=websocket,
    channel_name="dashboard.user-123",
    user_id="user-123",
    wallet_address="5Kq..."
)
    ↓
    client = Client(
        id=uuid4(),
        channel_name="dashboard.user-123",
        user_id="user-123",
        wallet_address="5Kq...",
        connected_at=datetime.utcnow()
    )
    
    channels["dashboard.user-123"].append(websocket)
    client_registry[id(websocket)] = client
    
    LOG: "Client added: channel=dashboard.user-123, client={id}, "
         "user=user-123, new_channel=False, channel_subs=2, "
         "total=8525, user_conns=4"

Step 7: Message Loop
────────────────────
while True:
    # Check shutdown
    if shutdown_manager.is_shutting_down():
        await websocket.send_json({"type": "shutdown"})
        await websocket.close(code=1001)
        break
    
    # Receive message with 30s timeout
    data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
    
    # Legacy ping/pong
    if data == "ping":
        await websocket.send_text("pong")
        continue
    
    # Validate message
    validation_result = ValidateMessageUseCase.validate_message(data)
    
    if not validation_result.valid:
        LOG: "Message validation failed [conn=conn_abc123] "
             "[errors={errors}]"
        await websocket.send_json({
            "type": "error",
            "code": "VALIDATION_ERROR",
            "errors": validation_result.errors
        })
        continue
    
    # Rate limiting check
    message_type = validation_result.message_type
    
    is_allowed = RateLimiter.check_rate_limit("user-123", message_type)
    
    if not is_allowed:
        retry_after = RateLimiter.get_retry_after_seconds("user-123", message_type)
        
        LOG: "Rate limit exceeded [conn=conn_abc123] "
             "[message_type={type}] [retry_after={retry_after}s]"
        
        await websocket.send_json({
            "type": "error",
            "code": "RATE_LIMIT_EXCEEDED",
            "message": f"Rate limit exceeded for message type '{message_type}'",
            "retry_after_seconds": retry_after
        })
        continue
    
    # Handle control messages (ping, subscribe, etc.)
    if ValidateMessageUseCase.is_control_message(message_type):
        await handle_control_message(websocket, message_type, data)
    else:
        await websocket.send_json({
            "type": "ack",
            "message_type": message_type,
            "size_bytes": validation_result.size_bytes
        })

Step 8: Disconnection
─────────────────────
except WebSocketDisconnect:
    LOG: "Client disconnected [conn=conn_abc123] [channel=dashboard.user-123]"

finally:
    # Remove client
    ConnectionManager.remove_client(websocket, "dashboard.user-123")
        ↓
        channels["dashboard.user-123"].remove(websocket)
        del client_registry[id(websocket)]
        
        LOG: "Client removed: channel=dashboard.user-123, "
             "client={id}, user=user-123, channel_subs=1, total=8524"
    
    # Cleanup empty ephemeral channel
    if ManageChannelUseCase.should_cleanup_channel("dashboard.user-123"):
        if len(channels["dashboard.user-123"]) == 0:
            del channels["dashboard.user-123"]
            LOG: "Ephemeral channel cleaned up [channel=dashboard.user-123]"
```

### 4.2 Event Publishing Flow
```
Chevalier → POST /publish

Request:
{
  "channel": "dashboard.user-123",
  "data": {
    "type": "dashboard.candle",
    "deployment_id": "deploy-xxx",
    "token_symbol": "SOL/USDC",
    "timestamp": "2026-01-20T15:30:00Z",
    "open": 145.20,
    "high": 145.50,
    "low": 145.10,
    "close": 145.35,
    "volume": 125000.0
  }
}

Headers:
X-Service-Name: chevalier

↓ PublishEventRoute.publish_event()

Step 1: Check Service Exemption
────────────────────────────────
is_exempt = "chevalier" in rate_limit_exempt_services
# rate_limit_exempt_services = ["chronicler", "chevalier", "cartographe"]
is_exempt = True  # Chevalier is exempt

Step 2: Rate Limiting (skipped for exempt services)
────────────────────────────────────────────────────
# Skipped because is_exempt = True

Step 3: Extract Event Type
───────────────────────────
event_type = data.get("type")  # "dashboard.candle"

Step 4: Validate Event Schema
──────────────────────────────
if event_type:
    ValidateEventUseCase.execute("dashboard.candle", event_data)
        ↓
        schema_class = EVENT_SCHEMAS["dashboard.candle"]
        # schema_class = DashboardCandleEvent
        
        # Validate total size
        total_size = calculate_size(event_data)  # 487 bytes
        if total_size > max_event_size (1MB):  # False
            raise EventSizeExceededError
        
        # Validate against Pydantic schema
        validated_event = DashboardCandleEvent.model_validate(event_data)
        
        # Check source matches header (if provided)
        event_source = event_data.get("metadata", {}).get("source")
        # event_source = None (dashboard events don't have metadata)
        
        # Use validated data
        message_data = validated_event.model_dump()

Step 5: Ensure Channel Exists
──────────────────────────────
ManageChannelUseCase.create_or_get_channel("dashboard.user-123")
    ↓
    # Channel already exists (from WebSocket connection)
    return Channel(name="dashboard.user-123", is_ephemeral=False)

Step 6: Get Channel Subscribers
────────────────────────────────
subscribers = ConnectionManager.get_channel_subscribers("dashboard.user-123")
# subscribers = [<WebSocket 0x7f...>, <WebSocket 0x8a...>]  # 2 connections

Step 7: Broadcast Message
──────────────────────────
sent_count = BroadcastMessageUseCase.execute(
    channel="dashboard.user-123",
    message_data=message_data,
    subscribers=subscribers
)
    ↓
    # Validate channel name
    ChannelName("dashboard.user-123")  # Valid
    
    # Validate message
    message = Message(message_data)  # Valid
    
    # Broadcast to subscribers
    sent_count = 0
    dead_clients = []
    
    for ws in subscribers:
        try:
            await ws.send_json(message.data)  # Success
            sent_count += 1
        except Exception:
            dead_clients.append(ws)
    
    return sent_count  # 2

Step 8: Update Statistics
──────────────────────────
Container.increment_stat("total_messages_sent", sent_count=2)
    ↓
    stats["total_messages_sent"] += 2  # Now: 145,892

Step 9: Return Response
───────────────────────
return PublishResponse(
    status="published",
    channel="dashboard.user-123",
    clients_reached=2,
    timestamp="2026-01-20T15:30:00.123Z"
)

Response (200 OK):
{
  "status": "published",
  "channel": "dashboard.user-123",
  "clients_reached": 2,
  "timestamp": "2026-01-20T15:30:00.123Z"
}
```

### 4.3 Heartbeat and Dead Connection Cleanup
```
Background Task: _heartbeat_loop()

interval = settings.heartbeat_interval  # 30 seconds

while True:
    # Stop if shutting down
    if shutdown_manager.is_shutting_down():
        LOG: "Heartbeat stopped (shutdown)"
        break
    
    await asyncio.sleep(interval)
    
    total = ConnectionManager.get_total_connections()
    
    if total == 0:
        continue  # No clients connected
    
    LOG: "Heartbeat -> {total} clients"
    
    # Send ping to all connections
    for channel, subscribers in ConnectionManager.channels.items():
        dead_clients = []
        
        for ws in subscribers:
            try:
                await ws.send_json({"type": "ping"})
            except Exception:
                # Connection is dead
                dead_clients.append(ws)
        
        # Cleanup dead connections
        for ws in dead_clients:
            ConnectionManager.remove_client(ws, channel)
            LOG: "Dead connection removed [channel={channel}]"
```

---

## 5. Channel Architecture

### 5.1 Channel Types

| Channel Pattern | Description | Authorization | Ephemeral |
|----------------|-------------|---------------|-----------|
| `global` | System-wide events | Public | No |
| `user.{user_id}` | User-specific events | Owner only | No |
| `dashboard.{user_id}` | Real-time trading data | Owner only | No |
| `strategy.{id}` | Strategy events | Public* | No |
| `backtest.{id}` | Backtest progress | Public | Yes |
| `forge.job.{id}` | Background job updates | Public | Yes |
| `price.{token}` | Market data | Public | No |
| `trade`, `candles`, etc. | Public channels | Public | No |

*Strategy channel authorization checks ownership in Architect (TODO).

### 5.2 Channel Lifecycle

**Persistent Channels:**
```
Created: On first subscriber
Exists: Until service restart
Example: global, user.*, dashboard.*, price.*
```

**Ephemeral Channels:**
```
Created: On first subscriber
Deleted: When subscriber count reaches 0
Example: backtest.*, forge.job.*
```

### 5.3 Multi-Channel Subscriptions

**Current Implementation**: One WebSocket = One Channel
- Frontend must open multiple WebSocket connections for multiple channels
- Example: User dashboard opens 3 connections:
  1. `ws://courier/ws/dashboard.user-123`
  2. `ws://courier/ws/price.sol`
  3. `ws://courier/ws/global`

**Future Enhancement**: Single WebSocket with dynamic subscriptions
```json
// Subscribe to additional channel
{"type": "subscribe", "channel": "price.pump"}

// Unsubscribe from channel
{"type": "unsubscribe", "channel": "price.sol"}

// Events tagged with channel
{"type": "dashboard.candle", "channel": "dashboard.user-123", ...}
```

---

## 6. Event Schema System

### 6.1 Base Event Structure

**All events inherit from `BaseEvent`:**
```python
class BaseEvent(BaseModel):
    type: str                     # Event type identifier
    metadata: EventMetadata       # Timestamp, source, correlation_id, user_id
    data: Dict[str, Any]          # Event-specific payload
```

**EventMetadata:**
```python
class EventMetadata(BaseModel):
    timestamp: str                # ISO 8601 with Z suffix
    source: str                   # Publishing service name
    correlation_id: Optional[str] # Distributed tracing ID
    user_id: Optional[str]        # User ID for user-scoped events
```

### 6.2 Event Categories

#### 6.2.1 Prophet Events (AI Strategy Generation)

**prophet.message_chunk**: Streaming AI response
```python
{
  "type": "prophet.message_chunk",
  "data": {
    "conversation_id": "conv_abc123",
    "chunk": "Based on your requirements, I suggest...",
    "is_final": false
  }
}
```

**prophet.tsdl_ready**: Complete strategy code
```python
{
  "type": "prophet.tsdl_ready",
  "data": {
    "conversation_id": "conv_abc123",
    "strategy_id": "strat_xyz789",
    "tsdl": "strategy MyStrategy...",
    "metadata": {...}
  }
}
```

**prophet.error**: Generation failure
```python
{
  "type": "prophet.error",
  "data": {
    "conversation_id": "conv_abc123",
    "error_code": "GENERATION_FAILED",
    "message": "Failed to generate valid TSDL"
  }
}
```

#### 6.2.2 Cartographe Events (Backtesting)

**backtest.started**: Backtest initiated
```python
{
  "type": "backtest.started",
  "metadata": {
    "timestamp": "2026-01-20T15:00:00Z",
    "source": "cartographe",
    "user_id": "user-123"
  },
  "data": {
    "backtest_id": "bt_abc",
    "job_id": "job_xyz",
    "user_id": "user-123",
    "strategy_id": "strat_123",
    "parameters": {...}
  }
}
```

**backtest.progress**: Progress update
```python
{
  "type": "backtest.progress",
  "data": {
    "backtest_id": "bt_abc",
    "job_id": "job_xyz",
    "user_id": "user-123",
    "progress": 0.45,
    "stage": "analyzing_trades",
    "message": "Analyzing 523 trades..."
  }
}
```

**backtest.completed**: Backtest finished
```python
{
  "type": "backtest.completed",
  "data": {
    "backtest_id": "bt_abc",
    "job_id": "job_xyz",
    "user_id": "user-123",
    "duration_seconds": 127,
    "summary": {...}
  }
}
```

#### 6.2.3 Chevalier Events (Live Trading)

**strategy.deployed**: Strategy activated
```python
{
  "type": "strategy.deployed",
  "data": {
    "strategy_id": "strat_xyz",
    "user_id": "user_123",
    "name": "RSI Momentum",
    "initial_capital": 1000.0,
    "token_pair": "SOL/USDC",
    "status": "active"
  }
}
```

**trade.signal_generated**: Trading signal
```python
{
  "type": "trade.signal_generated",
  "data": {
    "strategy_id": "strat_xyz",
    "user_id": "user_123",
    "signal_id": "sig_abc",
    "token": "SOL",
    "direction": "buy",
    "confidence": 0.85,
    "reason": "RSI oversold + volume spike",
    "price_at_signal": 145.67
  }
}
```

**trade.order_filled**: Order executed
```python
{
  "type": "trade.order_filled",
  "data": {
    "strategy_id": "strat_xyz",
    "user_id": "user_123",
    "order_id": "ord_123",
    "token": "SOL",
    "direction": "buy",
    "fill_price": 145.55,
    "fill_amount": 10.0,
    "total_value": 1455.50,
    "fees": 1.46,
    "tx_signature": "5Kq..."
  }
}
```

#### 6.2.4 Dashboard Events (Real-Time Streaming)

**Lightweight events for high-frequency updates (no full BaseEvent structure):**

**dashboard.candle**: OHLCV data
```python
{
  "type": "dashboard.candle",
  "deployment_id": "deploy-xxx",
  "token_symbol": "SOL/USDC",
  "timestamp": "2026-01-20T15:30:00Z",
  "open": 145.20,
  "high": 145.50,
  "low": 145.10,
  "close": 145.35,
  "volume": 125000.0
}
```

**dashboard.indicators**: Indicator values
```python
{
  "type": "dashboard.indicators",
  "deployment_id": "deploy-xxx",
  "values": {
    "RSI(16)": 32.5,
    "EMA(20)": 143.87,
    "SMA(50)": 142.15
  }
}
```

**dashboard.position**: Position state
```python
{
  "type": "dashboard.position",
  "deployment_id": "deploy-xxx",
  "has_position": true,
  "entry_price": 130.50,
  "current_price": 145.35,
  "size": 10.0,
  "unrealized_pnl": 148.50,
  "cash_balance": 9851.50,
  "total_equity": 10000.00,
  "realized_pnl": 485.00,
  "total_trades": 12
}
```

**dashboard.signal**: Trade signal notification
```python
{
  "type": "dashboard.signal",
  "deployment_id": "deploy-xxx",
  "signal_type": "ENTRY",
  "price": 145.35,
  "reasons": ["RSI(16) crosses_above 30"],
  "indicators": {"RSI(16)": 32.5}
}
```

### 6.3 Event Validation

**Validation Layers:**
```
1. Size Validation:
   ├── Total event size < 1MB
   ├── Payload (data) < 512KB
   └── Metadata < 10KB

2. Schema Validation:
   ├── Required fields present
   ├── Type checking (Pydantic)
   ├── Business rules (progress 0-1, etc.)
   └── Field constraints (max lengths, ranges)

3. Source Validation:
   └── X-Service-Name header matches metadata.source
```

**Error Responses:**
```python
# Size limit exceeded (413 Payload Too Large)
{
  "error": "Event size exceeded",
  "message": "payload size 600000 bytes exceeds maximum allowed 524288 bytes",
  "component": "payload",
  "size_bytes": 600000,
  "max_size_bytes": 524288,
  "limits": {
    "max_event_size": 1048576,
    "max_payload_size": 524288,
    "max_metadata_size": 10240
  }
}

# Schema validation failed (400 Bad Request)
{
  "error": "Event schema validation failed",
  "message": "Event data does not match required schema",
  "event_type": "backtest.progress",
  "validation_errors": [
    {
      "loc": ["data", "progress"],
      "msg": "ensure this value is less than or equal to 1.0",
      "type": "value_error.number.not_le"
    }
  ]
}
```

---

## 7. Authentication & Authorization

### 7.1 JWT Authentication

**Token Structure:**
```json
{
  "user_id": "user-123",
  "wallet_address": "5Kq2FV7xS...",
  "exp": 1737392400,
  "iat": 1737306000
}
```

**WebSocket Connection with JWT:**
```javascript
// Frontend
const token = localStorage.getItem("jwt_token");
const ws = new WebSocket(`ws://courier:8765/ws/dashboard.user-123?token=${token}`);
```

**Authentication Flow:**
```
1. Extract token from query parameter
2. JWTVerifier.verify_token(token)
   ↓
   jwt.decode(token, secret, algorithms=["HS256"])
   ↓
   Check expiration: exp > current_time
   ↓
   Return TokenPayload(user_id, wallet_address, exp, iat)

3. JWTVerifier.verify_channel_access(user_id, channel)
   ↓
   Apply authorization rules (see below)
   ↓
   Return True if authorized, False otherwise
```

**Error Handling:**
```python
# Token expired
raise TokenExpiredError("Token expired")
→ WebSocket closed with code 1008, reason: "Token expired"

# Token invalid
raise TokenInvalidError("Invalid token: signature verification failed")
→ WebSocket closed with code 1008, reason: "Invalid token"

# Unauthorized channel access
raise AuthorizationError("User not authorized for channel: dashboard.user-456")
→ WebSocket closed with code 1008, reason: "Unauthorized access"
```

### 7.2 Channel Authorization Rules

**Implementation in `JWTVerifier.verify_channel_access()`:**
```python
def verify_channel_access(user_id: str, channel: str) -> bool:
    # Global channel - everyone can access
    if channel == "global":
        return True
    
    # User channel - must match user_id
    if channel.startswith("user."):
        channel_user_id = channel.split(".", 1)[1]
        return channel_user_id == user_id
    
    # Dashboard channel - must match user_id
    if channel.startswith("dashboard."):
        channel_user_id = channel.split(".", 1)[1]
        return channel_user_id == user_id
    
    # Strategy channel - allow access for now
    # TODO: Query Architect to verify strategy ownership
    if channel.startswith("strategy."):
        return True
    
    # Backtest channel - ephemeral, allow access
    if channel.startswith("backtest."):
        return True
    
    # Forge job channel - ephemeral, allow access
    if channel.startswith("forge.job."):
        return True
    
    # Price channels - public market data
    if channel.startswith("price."):
        return True
    
    # Public channels - allow access
    if channel in ["trade", "candles", "sys", "rsi", "extrema", 
                   "analysis", "subscription", "payment", "deposit"]:
        return True
    
    # Unknown channel - deny by default
    return False
```

**Authorization Matrix:**

| Channel | Anonymous | Authenticated | Owner Only |
|---------|-----------|---------------|------------|
| `global` | ✅ | ✅ | N/A |
| `user.{user_id}` | ❌ | ❌ | ✅ |
| `dashboard.{user_id}` | ❌ | ❌ | ✅ |
| `strategy.{id}` | ❌ | ✅ | Future: ✅ |
| `backtest.{id}` | ❌ | ✅ | N/A |
| `forge.job.{id}` | ❌ | ✅ | N/A |
| `price.{token}` | ✅ | ✅ | N/A |
| Public channels | ✅ | ✅ | N/A |

### 7.3 Optional Authentication

**Configuration:**
```yaml
# config/default.yaml
require_auth: false  # Authentication optional by default
jwt_secret: null     # Set via JWT_SECRET environment variable
```

**Behavior:**
- If `require_auth: false`: All connections allowed, no JWT validation
- If `require_auth: true`: JWT token required for all WebSocket connections
- If `JWT_SECRET` not set: Raises error on startup when auth enabled

---

## 8. Rate Limiting

### 8.1 Rate Limiting Architecture

**Two Independent Rate Limiters:**

1. **Publish Rate Limiter**: Limits `/publish` endpoint calls per service
2. **WebSocket Rate Limiter**: Limits WebSocket messages per user/client with per-type overrides

**Token Bucket Algorithm**: Implemented in `shared.resilience.RateLimiter`

### 8.2 Publish Rate Limiting

**Purpose**: Prevent backend services from overwhelming Courier with publish requests.

**Configuration:**
```yaml
rate_limit_enabled: true
rate_limit_publish_requests: 100        # 100 requests per minute
rate_limit_window_seconds: 60           # 60 second window
rate_limit_exempt_services:             # Services exempt from rate limiting
  - chronicler
  - chevalier
  - cartographe
```

**Rate Limit Key**: Service name from `X-Service-Name` header

**Flow:**
```python
1. Extract X-Service-Name header
   service_name = "prophet"

2. Check if service is exempt
   if service_name in rate_limit_exempt_services:
       # Skip rate limiting
       proceed to Step 3

3. Check rate limit
   is_allowed = RateLimiter.check_rate_limit(service_name)
   
   if not is_allowed:
       # Get stats for error response
       stats = RateLimiter.get_stats(service_name)
       retry_after = stats["retry_after_seconds"]
       
       # Return 429 Too Many Requests
       return HTTPException(
           status_code=429,
           detail={
               "error": "Rate limit exceeded",
               "limit": 100,
               "window_seconds": 60,
               "retry_after_seconds": retry_after
           },
           headers={
               "X-RateLimit-Limit": "100",
               "X-RateLimit-Remaining": "0",
               "Retry-After": str(retry_after)
           }
       )
```

**Example Error Response:**
```json
HTTP/1.1 429 Too Many Requests
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1737307200
Retry-After: 42

{
  "error": "Rate limit exceeded",
  "message": "Too many requests from service 'prophet'",
  "limit": 100,
  "window_seconds": 60,
  "retry_after_seconds": 42,
  "reset_at": "2026-01-20T16:00:00Z"
}
```

### 8.3 WebSocket Message Rate Limiting

**Purpose**: Prevent clients from spamming WebSocket messages.

**Configuration:**
```yaml
rate_limit_enabled: true
rate_limit_websocket_connections: 10    # Default: 10 messages/min
rate_limit_window_seconds: 60
rate_limit_per_message_type:            # Per-type overrides
  trade: 50           # 50 trade messages/min
  candles: 100        # 100 candle messages/min
  strategy: 10        # 10 strategy messages/min
  subscription: 5     # 5 subscription messages/min
  payment: 5          # 5 payment messages/min
  deposit: 5          # 5 deposit messages/min
```

**Rate Limit Key**: `user_id` or `client_id` + optional `message_type`

**Per-Type Limits:**
- If message has type in `rate_limit_per_message_type`: Use type-specific limit
- Otherwise: Use default limit (`rate_limit_websocket_connections`)

**Flow:**
```python
1. Extract rate limit identifier
   rate_limit_identifier = user_id or client_id

2. Extract message type
   message_type = message.get("type")  # e.g., "trade"

3. Check rate limit
   is_allowed = RateLimiter.check_rate_limit(
       rate_limit_identifier,
       message_type=message_type
   )
   
   # Uses registry key: "user-123:trade"
   # Limit: 50 trades/min (from per_type_limits)

4. If rate limited:
   retry_after = RateLimiter.get_retry_after_seconds(
       rate_limit_identifier,
       message_type
   )
   
   # Send error to client
   await websocket.send_json({
       "type": "error",
       "code": "RATE_LIMIT_EXCEEDED",
       "message": f"Rate limit exceeded for message type '{message_type}'",
       "retry_after_seconds": retry_after,
       "message_type": message_type
   })
   
   # Increment counter
   Container.increment_rate_limit_hit(message_type)
```

**Example Error Message:**
```json
{
  "type": "error",
  "code": "RATE_LIMIT_EXCEEDED",
  "message": "Rate limit exceeded for message type 'trade'",
  "retry_after_seconds": 8,
  "message_type": "trade"
}
```

### 8.4 Token Bucket Implementation

**From `shared.resilience.rate_limiter.RateLimiterRegistry`:**
```python
class TokenBucket:
    def __init__(self, tokens_per_second: float, burst_size: int):
        self.tokens_per_second = tokens_per_second
        self.burst_size = burst_size
        self.tokens = burst_size
        self.last_refill = time.time()
    
    def try_acquire(self, tokens: float = 1.0) -> bool:
        # Refill tokens based on elapsed time
        now = time.time()
        elapsed = now - self.last_refill
        self.tokens = min(
            self.burst_size,
            self.tokens + elapsed * self.tokens_per_second
        )
        self.last_refill = now
        
        # Try to consume tokens
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False
```

**Configuration Calculation:**
```python
# For limit=100 requests per window=60 seconds
tokens_per_second = limit / window_seconds
                  = 100 / 60
                  = 1.67 tokens/second

burst_size = limit  # 100 tokens

# Allows bursts up to 100 requests, then throttles to 1.67 req/s
```

---

## 9. Deployment Architecture

### 9.1 Docker Multi-Stage Build

**Dockerfile Structure:**
```dockerfile
# Stage 1: Python Builder
FROM python:3.12-slim AS python-builder
- Install build dependencies (gcc, g++)
- Copy pyproject.toml and src/
- Install courier package
- Fetch shared==0.6.0 from Private PyPI (http://172.17.0.1:10001)

# Stage 2: Development
FROM python:3.12-slim AS development
- Copy Python packages from builder
- Install editable mode: pip install -e ".[dev]"
- Expose ports: 9765 (API), 9790 (Metrics), 9791 (Health)
- CMD: python -m courier.main

# Stage 3: Production
FROM python:3.12-slim AS production
- Create non-root user: courier_user
- Copy Python packages from builder
- Copy application code with proper ownership
- Expose ports: 8765 (API), 8790 (Metrics), 8791 (Health)
- USER: courier_user
- CMD: python -m courier.main
```

### 9.2 Port Allocation

| Environment | API Port | Metrics Port | Health Port |
|-------------|----------|--------------|-------------|
| Production  | 8765     | 8790         | 8791        |
| Development | 9765     | 9790         | 9791        |
| Test        | 7765     | 7790         | 7791        |

### 9.3 Environment Configuration

**Production** (`.env.production`):
```bash
ENV=production
DEBUG=false
PORT=8765
JWT_SECRET=<strong_secret>
REQUIRE_AUTH=true
RATE_LIMIT_ENABLED=true
MAX_TOTAL_CONNECTIONS=10000
MAX_CONNECTIONS_PER_USER=5
METRICS_ENABLED=true
METRICS_PORT=8790
HEALTH_CHECK_ENABLED=true
HEALTH_PORT=8791
```

**Development** (`.env.development`):
```bash
ENV=development
DEBUG=true
PORT=9765
JWT_SECRET=dev_secret_not_secure
REQUIRE_AUTH=false
RATE_LIMIT_ENABLED=true
MAX_TOTAL_CONNECTIONS=1000
MAX_CONNECTIONS_PER_USER=10
METRICS_ENABLED=true
METRICS_PORT=9790
HEALTH_CHECK_ENABLED=true
HEALTH_PORT=9791
```

### 9.4 Configuration Loading

**Hybrid Configuration System:**
```
Priority: ENV vars > environment-specific YAML > default YAML > Pydantic defaults

1. Load .env file (e.g., .env.production)
   ↓
2. Load config/default.yaml (base defaults)
   ↓
3. Load config/production.yaml (environment overrides)
   ↓
4. Create Settings instance (ENV vars override YAML)
   ↓
5. Validate with Pydantic
```

**Configuration Files:**
- `config/default.yaml`: Base defaults for all environments
- `config/production.yaml`: Production overrides
- `config/development.yaml`: Development overrides
- `config/test.yaml`: Test overrides

### 9.5 Service Dependencies

**Startup Order:**
1. Pourtier (API Gateway) - provides JWT authentication
2. **Courier** (this component) - ready to accept WebSocket connections
3. Backend Services (Chevalier, Chronicler, etc.) - publish events to Courier

**Health Checks:**
```bash
# Liveness probe (Kubernetes)
curl http://localhost:8765/health/live
# Response: {"status": "healthy", ...}

# Readiness probe (Kubernetes)
curl http://localhost:8765/health/ready
# Response: {"status": "healthy", "checks": {...}}

# Metrics endpoint
curl http://localhost:8790/metrics
# Prometheus format metrics
```

---

## 10. API Reference

### 10.1 WebSocket Connection

#### WS /ws/{channel}

Establish WebSocket connection to channel.

**URL Parameters:**
- `channel`: Channel name (required)

**Query Parameters:**
- `token`: JWT token (optional, required if `require_auth: true`)

**Connection Examples:**
```javascript
// Unauthenticated (if auth disabled)
const ws = new WebSocket("ws://courier:8765/ws/global");

// Authenticated
const token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...";
const ws = new WebSocket(`ws://courier:8765/ws/dashboard.user-123?token=${token}`);

// Price data channel
const ws = new WebSocket("ws://courier:8765/ws/price.sol");
```

**Client → Server Messages:**

**Ping/Pong (Legacy):**
```json
// Send
"ping"

// Receive
"pong"
```

**Control Messages:**
```json
// Ping (JSON format)
{"type": "ping"}
→ {"type": "pong"}

// Subscribe (future)
{"type": "subscribe", "channel": "price.pump"}
→ {"type": "subscribed", "channel": "price.pump"}

// Unsubscribe (future)
{"type": "unsubscribe", "channel": "price.sol"}
→ {"type": "unsubscribed", "channel": "price.sol"}
```

**Server → Client Messages:**

**Heartbeat:**
```json
{"type": "ping"}
```

**Event Broadcast:**
```json
{
  "type": "dashboard.candle",
  "deployment_id": "deploy-xxx",
  "token_symbol": "SOL/USDC",
  "timestamp": "2026-01-20T15:30:00Z",
  "open": 145.20,
  "high": 145.50,
  "low": 145.10,
  "close": 145.35,
  "volume": 125000.0
}
```

**Error Messages:**
```json
// Validation error
{
  "type": "error",
  "code": "VALIDATION_ERROR",
  "message": "Message validation failed",
  "errors": ["String field 'data' too long: 15000 chars (max: 10000)"]
}

// Rate limit exceeded
{
  "type": "error",
  "code": "RATE_LIMIT_EXCEEDED",
  "message": "Rate limit exceeded for message type 'trade'",
  "retry_after_seconds": 8,
  "message_type": "trade"
}

// Connection limit exceeded
{
  "type": "error",
  "code": "CONNECTION_LIMIT_EXCEEDED",
  "message": "User connection limit reached: 5",
  "limit_type": "per_user"
}

// Shutdown notification
{
  "type": "shutdown",
  "message": "Server is shutting down",
  "code": 1001
}
```

**Close Codes:**
- `1000`: Normal closure
- `1001`: Server going away (shutdown)
- `1008`: Policy violation (auth failed, rate limited)

### 10.2 Event Publishing

#### POST /publish

Publish event to channel with schema validation and size limits.

**Request:**
```json
{
  "channel": "dashboard.user-123",
  "data": {
    "type": "dashboard.candle",
    "deployment_id": "deploy-xxx",
    ...
  }
}
```

**Headers:**
```
Content-Type: application/json
X-Service-Name: chevalier  (recommended for rate limiting)
```

**Response (200 OK):**
```json
{
  "status": "published",
  "channel": "dashboard.user-123",
  "clients_reached": 2,
  "timestamp": "2026-01-20T15:30:00.123Z"
}
```

**Error Responses:**

**400 Bad Request** - Invalid channel or validation failed:
```json
{
  "error": "Event validation failed",
  "message": "Unknown event type: unknown.type",
  "event_type": "unknown.type"
}
```

**413 Payload Too Large** - Size limit exceeded:
```json
{
  "error": "Event size exceeded",
  "message": "payload size 600000 bytes exceeds maximum allowed 524288 bytes",
  "component": "payload",
  "size_bytes": 600000,
  "max_size_bytes": 524288,
  "limits": {
    "max_event_size": 1048576,
    "max_payload_size": 524288,
    "max_metadata_size": 10240
  }
}
```

**429 Too Many Requests** - Rate limit exceeded:
```json
{
  "error": "Rate limit exceeded",
  "message": "Too many requests from service 'prophet'",
  "limit": 100,
  "window_seconds": 60,
  "retry_after_seconds": 42,
  "reset_at": "2026-01-20T16:00:00Z"
}
```

#### POST /publish/{channel}

Legacy endpoint with channel in URL.

**Request:**
```json
{
  "type": "trade.signal_generated",
  "data": {...}
}
```

**Note**: Internally converts to new format and calls main `/publish` endpoint.

### 10.3 Health & Statistics

#### GET /health/live

Liveness probe for Kubernetes.

**Response (200 OK):**
```json
{
  "status": "healthy",
  "checks": {
    "service": {
      "name": "courier",
      "status": "healthy",
      "message": "Service is alive",
      "timestamp": "2026-01-20T15:30:00Z"
    }
  },
  "version": "1.0.0",
  "timestamp": "2026-01-20T15:30:00Z"
}
```

#### GET /health/ready

Readiness probe for Kubernetes.

**Response (200 OK):**
```json
{
  "status": "healthy",
  "checks": {
    "connection_capacity": {
      "name": "connection_capacity",
      "status": "healthy",
      "message": "Capacity available: 8524/10000 (85.2%)",
      "duration": 0.001,
      "timestamp": "2026-01-20T15:30:00Z",
      "metadata": {
        "total_connections": 8524,
        "max_connections": 10000,
        "capacity_percent": 85.2
      }
    },
    "connection_manager": {
      "name": "connection_manager",
      "status": "healthy",
      "message": "Operational (47 active channels)",
      "duration": 0.0005,
      "timestamp": "2026-01-20T15:30:00Z",
      "metadata": {
        "active_channels": 47,
        "channel_names": ["global", "user.123", ...]
      }
    }
  },
  "version": "1.0.0",
  "timestamp": "2026-01-20T15:30:00Z"
}
```

**Response (503 Service Unavailable)** - Not ready:
```json
{
  "status": "degraded",
  "checks": {
    "connection_capacity": {
      "status": "degraded",
      "message": "High capacity usage: 9500/10000 (95.0%)"
    }
  }
}
```

#### GET /health

Alias for `/health/ready`.

#### GET /stats

Detailed service statistics.

**Response (200 OK):**
```json
{
  "total_connections": 8524,
  "active_channels": 47,
  "channels": {
    "global": 523,
    "user.123": 3,
    "dashboard.user-123": 2,
    "price.sol": 1247,
    "price.pump": 892,
    ...
  },
  "total_messages_sent": 145892,
  "total_messages_received": 8934,
  "validation_failures": 12,
  "rate_limit_hits": 45,
  "limits": {
    "max_total_connections": 10000,
    "max_connections_per_user": 5,
    "max_clients_per_channel": 0
  }
}
```

---

## 11. Monitoring & Observability

### 11.1 Prometheus Metrics

**Metrics Server**: Runs on separate thread, port 8790 (prod) or 9790 (dev).

**Endpoint**: `http://courier:8790/metrics`

**Key Metrics:**
```python
# Connection metrics
courier_total_connections
courier_active_channels
courier_connections_per_channel{channel="global"}

# Message metrics
courier_messages_sent_total
courier_messages_received_total
courier_message_validation_failures_total

# Rate limiting metrics
courier_rate_limit_hits_total
courier_rate_limit_hits_per_type{message_type="trade"}

# Connection rejection metrics
courier_connection_rejections_total
courier_connection_rejections_by_type{limit_type="per_user"}

# Health metrics
courier_health_status{component="connection_capacity"}
courier_connection_capacity_percent
```

**Example Queries:**
```promql
# Connection count over time
courier_total_connections

# Message delivery rate
rate(courier_messages_sent_total[5m])

# Rate limit hit rate
rate(courier_rate_limit_hits_total[5m])

# Capacity usage percentage
courier_connection_capacity_percent > 90
```

### 11.2 Logging

**Log Levels:**
- `DEBUG`: Detailed message traces, heartbeat pings
- `INFO`: Connection events, broadcasts, lifecycle events
- `WARNING`: Rate limits exceeded, connection rejections, dead connections
- `ERROR`: WebSocket errors, validation failures
- `CRITICAL`: Shutdown events, system failures

**Key Log Patterns:**
```python
# Connection lifecycle
INFO: "WebSocket connection attempt [conn=conn_abc123] [channel=dashboard.user-123] [user=user-123]"
INFO: "Client connected successfully [conn=conn_abc123] [channel=dashboard.user-123] [client=uuid] [total_connections=8525]"
INFO: "Client disconnected [conn=conn_abc123] [channel=dashboard.user-123]"
INFO: "Client removed: channel=dashboard.user-123, client=uuid, user=user-123, channel_subs=1, total=8524"

# Connection limits
WARNING: "Global connection limit exceeded (current=10001, limit=10000, channel=price.sol, user=user-456)"
WARNING: "Per-user connection limit exceeded (user=user-123, current=6, limit=5, channel=dashboard.user-123)"
WARNING: "Connection rejected: per_user limit exceeded [conn=conn_xyz] [channel=dashboard.user-123]"

# Rate limiting
WARNING: "Rate limit exceeded [conn=conn_abc123] [message_type=trade] [retry_after=8s]"

# Broadcasting
DEBUG: "Message processed [conn=conn_abc123] [type=trade] [time=0.42ms] [size=487]"

# Heartbeat
DEBUG: "Heartbeat -> 8524 clients"
WARNING: "Dead connection removed [channel=price.sol]"

# Graceful shutdown
WARNING: "Graceful shutdown initiated"
INFO: "Notifying 8524 clients of shutdown"
INFO: "Waiting 5s for graceful close"
INFO: "Closed 47 connections"
INFO: "Courier stopped"
```

**Log Formats:**
```python
# SystemReporter context-tagged logs
reporter.info(
    "Client added: channel=dashboard.user-123, client={id}, user=user-123",
    context="ConnectionManager",
    verbose_level=2
)

# Output
[2026-01-20 15:30:00] [INFO] [ConnectionManager] Client added: channel=dashboard.user-123, client=abc-123, user=user-123
```

### 11.3 Health Monitoring

**Health Check Components:**

**Liveness Check:**
- Service alive and responding
- Returns 200 if process is running
- Used by Kubernetes to restart unhealthy pods

**Readiness Check:**
- Connection capacity check (not over 90%)
- Connection manager operational
- Returns 200 if ready for traffic
- Returns 503 if not ready (e.g., capacity exhausted)
- Used by Kubernetes to route traffic

**Health Check Intervals:**
```yaml
# Kubernetes configuration
livenessProbe:
  httpGet:
    path: /health/live
    port: 8791
  initialDelaySeconds: 40
  periodSeconds: 30
  timeoutSeconds: 10
  failureThreshold: 3

readinessProbe:
  httpGet:
    path: /health/ready
    port: 8791
  initialDelaySeconds: 10
  periodSeconds: 5
  timeoutSeconds: 3
  failureThreshold: 2
```

### 11.4 Distributed Tracing

**OpenTelemetry Support** (planned):
```yaml
TRACING_ENABLED: false
JAEGER_ENDPOINT: "http://jaeger:4318"
TRACE_SAMPLE_RATE: 0.1  # Sample 10% of requests
```

**Trace Context Propagation:**
- Extract `correlation_id` from event metadata
- Propagate through WebSocket messages
- Link publish → broadcast → client delivery

---

## 12. Troubleshooting Guide

### 12.1 Common Issues

#### Issue: WebSocket connection refused

**Symptoms:**
```
WebSocket connection to 'ws://courier:8765/ws/global' failed: 
Error during WebSocket handshake: net::ERR_CONNECTION_REFUSED
```

**Diagnosis:**
```bash
# Check if Courier is running
docker ps | grep courier

# Check Courier logs
docker logs lumiere-dev-courier | tail -50

# Check port binding
docker exec lumiere-dev-courier netstat -tuln | grep 9765

# Test connection from host
curl http://localhost:9765/health
```

**Solution:**
```bash
# Restart Courier
docker restart lumiere-dev-courier

# Check startup logs
docker logs -f lumiere-dev-courier | grep "Host:"
```

#### Issue: "Token expired" on WebSocket connection

**Symptoms:**
```
WebSocket closed with code 1008: Token expired
```

**Cause**: JWT token expired (typically 24-hour expiration).

**Solution:**
```javascript
// Frontend - refresh token before expiration
const token = await refreshJWTToken();
const ws = new WebSocket(`ws://courier:8765/ws/dashboard.user-123?token=${token}`);
```

#### Issue: "Connection limit exceeded"

**Symptoms:**
```json
{
  "type": "error",
  "code": "CONNECTION_LIMIT_EXCEEDED",
  "message": "User connection limit reached: 5",
  "limit_type": "per_user"
}
```

**Diagnosis:**
```bash
# Check connection stats
curl http://localhost:9765/stats | jq

# Check user connections
docker logs lumiere-dev-courier | grep "user=user-123" | grep "Client connected"
```

**Solution:**
```bash
# Close unused connections in frontend
ws1.close();
ws2.close();

# Or increase limit in config
# config/development.yaml
max_connections_per_user: 10  # Increase from 5
```

#### Issue: "Rate limit exceeded" on publish

**Symptoms:**
```json
HTTP/1.1 429 Too Many Requests
{
  "error": "Rate limit exceeded",
  "message": "Too many requests from service 'prophet'",
  "retry_after_seconds": 42
}
```

**Diagnosis:**
```bash
# Check publish rate limit stats
curl http://localhost:9765/stats | jq '.rate_limit_hits'

# Check service exemptions
cat config/development.yaml | grep rate_limit_exempt_services
```

**Solution:**
```bash
# Add service to exempt list
# config/development.yaml
rate_limit_exempt_services:
  - chronicler
  - chevalier
  - cartographe
  - prophet  # Add this

# Or increase limit
rate_limit_publish_requests: 200  # Increase from 100
```

#### Issue: Messages not reaching WebSocket clients

**Symptoms:** Backend publishes events, but frontend doesn't receive them.

**Diagnosis:**
```bash
# Check if channel has subscribers
curl http://localhost:9765/stats | jq '.channels["dashboard.user-123"]'

# Check Courier logs for broadcast
docker logs lumiere-dev-courier | grep "dashboard.user-123" | grep "clients_reached"

# Check if WebSocket connection is alive
# Frontend console
ws.readyState  // Should be 1 (OPEN)
```

**Solution:**
```bash
# Verify channel name matches exactly
# Backend
POST /publish {"channel": "dashboard.user-123", ...}

# Frontend
ws = new WebSocket("ws://courier:8765/ws/dashboard.user-123")

# Check for typos, case sensitivity, extra spaces
```

#### Issue: High memory usage

**Symptoms:**
```bash
docker stats lumiere-dev-courier
# MEM USAGE: 2.5GB / 4GB
```

**Diagnosis:**
```bash
# Check connection count
curl http://localhost:9765/stats | jq '.total_connections'

# Check channel count
curl http://localhost:9765/stats | jq '.active_channels'

# Check for memory leaks in logs
docker logs lumiere-dev-courier | grep "ERROR"
```

**Solution:**
```bash
# Reduce connection limits
max_total_connections: 5000  # Reduce from 10000

# Enable connection cleanup
# Restart Courier to trigger cleanup
docker restart lumiere-dev-courier

# Monitor memory after restart
docker stats lumiere-dev-courier
```

### 12.2 Debugging Workflows

#### Debug WebSocket Connection
```bash
# Enable DEBUG logging
export LOG_LEVEL=debug
docker restart lumiere-dev-courier

# Watch connection logs in real-time
docker logs -f lumiere-dev-courier | grep -E "WebSocket|Client"

# Test connection from command line
websocat ws://localhost:9765/ws/global

# Send test message
{"type": "ping"}
```

#### Debug Event Publishing
```bash
# Test publish endpoint
curl -X POST http://localhost:9765/publish \
  -H "Content-Type: application/json" \
  -H "X-Service-Name: test" \
  -d '{
    "channel": "global",
    "data": {
      "type": "test.message",
      "message": "Hello World"
    }
  }'

# Watch for broadcast in logs
docker logs -f lumiere-dev-courier | grep "published"

# Check if clients received message (in frontend console)
ws.onmessage = (event) => console.log("Received:", event.data);
```

#### Debug Rate Limiting
```bash
# Check rate limiter state
curl http://localhost:9765/stats | jq '.rate_limit_hits'

# Test rate limit manually
for i in {1..150}; do
  curl -X POST http://localhost:9765/publish \
    -H "X-Service-Name: test" \
    -d '{"channel":"global","data":{"test":true}}' &
done
wait

# Should see 429 responses after 100 requests
```

#### Debug Graceful Shutdown
```bash
# Test graceful shutdown
docker kill -s SIGTERM lumiere-dev-courier

# Watch shutdown logs
docker logs -f lumiere-dev-courier | grep -E "shutdown|Graceful"

# Expected output:
# Graceful shutdown initiated
# Notifying X clients of shutdown
# Waiting 5s for graceful close
# Closed X connections
# Courier stopped
```

### 12.3 Data Verification
```bash
# Check active connections
curl http://localhost:9765/stats | jq '{
  total_connections: .total_connections,
  active_channels: .active_channels,
  channels: .channels
}'

# Check message statistics
curl http://localhost:9765/stats | jq '{
  messages_sent: .total_messages_sent,
  messages_received: .total_messages_received,
  validation_failures: .validation_failures,
  rate_limit_hits: .rate_limit_hits
}'

# Check health status
curl http://localhost:9791/health | jq

# Check Prometheus metrics
curl http://localhost:9790/metrics | grep courier_
```

---

## Appendix A: Configuration Reference

### Environment Variables
```bash
# Application
APP_NAME=Courier
APP_VERSION=0.1.0
ENV=production|development|test
DEBUG=true|false

# API Server
PORT=8765  # Production: 8765, Development: 9765
HOST=0.0.0.0

# Service Discovery
POURTIER_URL=http://pourtier:8000
PASSEUR_URL=http://passeur:8766

# Authentication
JWT_SECRET=<secret_key>
JWT_ALGORITHM=HS256
REQUIRE_AUTH=true|false

# Connection Limits
MAX_TOTAL_CONNECTIONS=10000
MAX_CONNECTIONS_PER_USER=5
MAX_CLIENTS_PER_CHANNEL=0  # 0 = unlimited

# Rate Limiting
RATE_LIMIT_ENABLED=true|false
RATE_LIMIT_PUBLISH_REQUESTS=100
RATE_LIMIT_WEBSOCKET_CONNECTIONS=10
RATE_LIMIT_WINDOW_SECONDS=60

# Message Validation
MAX_MESSAGE_SIZE=1048576  # 1MB
MAX_STRING_LENGTH=10000
MAX_ARRAY_SIZE=1000

# Event Validation
MAX_EVENT_SIZE=1048576  # 1MB
MAX_EVENT_PAYLOAD_SIZE=524288  # 512KB
MAX_EVENT_METADATA_SIZE=10240  # 10KB

# Graceful Shutdown
SHUTDOWN_TIMEOUT=30
SHUTDOWN_GRACE_PERIOD=5

# Heartbeat
HEARTBEAT_INTERVAL=30

# Observability
METRICS_ENABLED=true
METRICS_HOST=0.0.0.0
METRICS_PORT=8790
HEALTH_CHECK_ENABLED=true
HEALTH_HOST=0.0.0.0
HEALTH_PORT=8791

# Logging
LOG_LEVEL=info|debug|warning|error|critical
LOG_FILE=null  # stdout for Docker
```

---

## Appendix B: Event Schema Registry

### Supported Event Types

**Prophet (AI Strategy Generation):**
- `prophet.message_chunk`
- `prophet.tsdl_ready`
- `prophet.error`

**Cartographe (Backtesting):**
- `backtest.started`
- `backtest.progress`
- `backtest.completed`
- `backtest.failed`
- `backtest.cancelled`

**Chevalier (Live Trading):**
- `strategy.deployed`
- `trade.signal_generated`
- `trade.order_placed`
- `trade.order_filled`
- `position.closed`

**Forge (Background Jobs):**
- `forge.job.started`
- `forge.job.progress`
- `forge.job.completed`
- `forge.job.failed`

**Dashboard (Real-Time Streaming):**
- `dashboard.candle`
- `dashboard.indicators`
- `dashboard.position`
- `dashboard.signal`
- `dashboard.error`
- `strategy.error`

---

**END OF DOCUMENT**

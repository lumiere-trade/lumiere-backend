# Courier TODO - Production Readiness Roadmap

**Last Updated:** October 28, 2025  
**Current Status:** E2E Tests Complete (103+ tests, 100% passing)  
**Target:** Production-ready event bus in 4 weeks

---

## ✅ Completed

### Core Implementation
- [x] FastAPI WebSocket server
- [x] Channel-based routing (global, user.*, strategy.*, forge.job.*, backtest.*)
- [x] Dynamic channel creation
- [x] HTTP publish endpoints (POST /publish, POST /publish/{channel})
- [x] WebSocket endpoint (WS /ws/{channel})
- [x] Connection management (heartbeat, cleanup)
- [x] Health check (GET /health)
- [x] Statistics (GET /stats)
- [x] JWT Authentication infrastructure
- [x] JWT token verification
- [x] Channel access authorization

### Testing
- [x] Unit tests (100% passing)
- [x] Integration tests (52/52 passing)
- [x] E2E tests (51/51 passing)
- [x] Total: 103+ tests, 100% coverage

---

## 📋 Phase 1: MVP Security & Validation (Week 1)

**Priority:** CRITICAL - Cannot deploy without this  
**Goal:** Secure Courier and validate all data

### Task 1.1: Complete WebSocket Authentication Implementation ⏳

**Status:** Partially complete (JWT infrastructure exists)  
**Time:** 1 day  
**Priority:** HIGH

**Remaining Work:**

#### Subtask 1.1.1: Enable Authentication in WebSocket Endpoint
- [ ] Modify `src/courier/presentation/api/websocket.py`
  - [ ] Add `token` query parameter requirement
  - [ ] Integrate `AuthenticateWebSocketUseCase`
  - [ ] Return 1008 policy violation for missing/invalid tokens
  - [ ] Log user_id with all connections

**Files to modify:**
```
courier/
├── src/courier/presentation/api/websocket.py    # Add auth
├── config/production.yaml                        # Verify JWT config
├── config/development.yaml                       # Verify JWT config
```

**Acceptance Criteria:**
- [ ] WebSocket connection requires valid JWT token
- [ ] Token expiration is enforced
- [ ] User can only access authorized channels
- [ ] Unauthorized access returns 1008 policy violation
- [ ] User ID is logged with all connections

**Testing:**
- [ ] Update E2E tests to use JWT tokens
- [ ] Add test for missing token rejection
- [ ] Add test for expired token rejection
- [ ] Add test for unauthorized channel access

---

### Task 1.2: Event Schema Validation ⭐ NEXT

**Status:** Not started  
**Time:** 2 days  
**Priority:** CRITICAL

**Objective:** Validate all published events against Pydantic schemas

#### Subtask 1.2.1: Create Base Event Schema

**Files to create:**
```
courier/
├── src/courier/domain/events/
│   ├── __init__.py
│   ├── base.py              # Base event classes
│   ├── prophet.py           # Prophet event schemas
│   ├── cartographe.py       # Cartographe event schemas
│   ├── chevalier.py         # Chevalier event schemas
│   └── forge.py             # Forge event schemas
```

**Implementation Steps:**

1. **Create Base Event** (`domain/events/base.py`)
```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any

class EventMetadata(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source: str
    correlation_id: Optional[str] = None
    user_id: Optional[str] = None

class BaseEvent(BaseModel):
    type: str
    metadata: EventMetadata
    data: Dict[str, Any]
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
```

2. **Create Prophet Events** (`domain/events/prophet.py`)
- [ ] `StrategyGenerationStartedEvent`
- [ ] `StrategyGenerationProgressEvent`
- [ ] `StrategyGenerationCompletedEvent`
- [ ] `StrategyGenerationFailedEvent`

3. **Create Cartographe Events** (`domain/events/cartographe.py`)
- [ ] `BacktestStartedEvent`
- [ ] `BacktestProgressEvent`
- [ ] `BacktestCompletedEvent`
- [ ] `BacktestFailedEvent`

4. **Create Chevalier Events** (`domain/events/chevalier.py`)
- [ ] `TradeExecutedEvent`
- [ ] `OrderPlacedEvent`
- [ ] `OrderFilledEvent`
- [ ] `OrderCancelledEvent`
- [ ] `PositionUpdatedEvent`

5. **Create Forge Events** (`domain/events/forge.py`)
- [ ] `ForgeJobStartedEvent`
- [ ] `ForgeJobProgressEvent`
- [ ] `ForgeJobCompletedEvent`
- [ ] `ForgeJobFailedEvent`

#### Subtask 1.2.2: Event Validation Use Case

**Files to create:**
```
courier/
├── src/courier/application/use_cases/
│   └── validate_event.py
```

**Implementation:**
- [ ] Create `ValidateEventUseCase`
- [ ] Map event types to Pydantic schemas
- [ ] Validate event against schema
- [ ] Return validation errors

#### Subtask 1.2.3: Integrate Validation in Publish Endpoints

**Files to modify:**
```
courier/
├── src/courier/presentation/api/publish.py
```

**Changes:**
- [ ] Add event validation before publishing
- [ ] Return 400 Bad Request for invalid events
- [ ] Log validation errors
- [ ] Add `X-Event-Type` header for type identification

**Acceptance Criteria:**
- [ ] All event types have Pydantic schemas
- [ ] Invalid events return 400 Bad Request
- [ ] Validation errors include clear messages
- [ ] Event type is logged with all publications
- [ ] Payload size limited to 100KB

**Testing:**
- [ ] Unit tests for all event schemas
- [ ] Unit tests for ValidateEventUseCase
- [ ] Integration tests for validation in publish endpoint
- [ ] Test oversized payload rejection

---

### Task 1.3: Rate Limiting

**Status:** Not started  
**Time:** 1 day  
**Priority:** HIGH

**Objective:** Prevent abuse with per-user rate limits

#### Subtask 1.3.1: Rate Limiter Infrastructure

**Files to create:**
```
courier/
├── src/courier/infrastructure/rate_limiting/
│   ├── __init__.py
│   ├── rate_limiter.py
│   └── memory_store.py
```

**Implementation:**
- [ ] Create `RateLimiter` class
- [ ] In-memory token bucket algorithm
- [ ] Configurable limits per user/channel
- [ ] Sliding window implementation

**Limits:**
```python
RATE_LIMITS = {
    "websocket_connections_per_user": 10,
    "publish_requests_per_minute": 100,
    "publish_requests_per_second": 10,
}
```

#### Subtask 1.3.2: Integrate Rate Limiting

**Files to modify:**
```
courier/
├── src/courier/presentation/api/websocket.py
├── src/courier/presentation/api/publish.py
```

**Changes:**
- [ ] Add rate limit check before WebSocket accept
- [ ] Add rate limit check before publish
- [ ] Return 429 Too Many Requests
- [ ] Add `Retry-After` header

**Acceptance Criteria:**
- [ ] WebSocket connections limited per user
- [ ] Publish requests limited per user
- [ ] Rate limits configurable via settings
- [ ] 429 status code with Retry-After header
- [ ] Rate limit metrics exported

**Testing:**
- [ ] Unit tests for RateLimiter
- [ ] Integration tests for rate limiting
- [ ] Load test to verify limits enforced

---

### Task 1.4: Graceful Shutdown

**Status:** Not started  
**Time:** 1 day  
**Priority:** MEDIUM

**Objective:** Clean shutdown without dropping connections

#### Subtask 1.4.1: Shutdown Handler

**Files to modify:**
```
courier/
├── src/courier/main.py
```

**Implementation:**
- [ ] Add signal handlers (SIGTERM, SIGINT)
- [ ] Create `graceful_shutdown()` function
- [ ] Stop accepting new connections
- [ ] Wait for pending messages (timeout 30s)
- [ ] Close all WebSocket connections gracefully
- [ ] Update health check to "shutting_down"

**Acceptance Criteria:**
- [ ] SIGTERM triggers graceful shutdown
- [ ] Pending messages delivered before shutdown
- [ ] All connections closed cleanly
- [ ] Health check returns 503 during shutdown
- [ ] Shutdown completes within 30 seconds

**Testing:**
- [ ] Test graceful shutdown with active connections
- [ ] Test shutdown with pending messages
- [ ] Test health check during shutdown

---

## 📋 Phase 2: Production Hardening (Week 2)

**Priority:** HIGH  
**Goal:** Monitoring, observability, production-ready

### Task 2.1: Prometheus Metrics

**Status:** Not started  
**Time:** 2 days  
**Priority:** HIGH

**Objective:** Export metrics for monitoring

#### Subtask 2.1.1: Metrics Infrastructure

**Files to create:**
```
courier/
├── src/courier/infrastructure/metrics/
│   ├── __init__.py
│   └── prometheus_metrics.py
```

**Metrics to implement:**
```python
# Counters
courier_connections_total
courier_disconnections_total
courier_messages_published_total
courier_messages_delivered_total
courier_auth_failures_total
courier_validation_failures_total
courier_rate_limit_hits_total

# Gauges
courier_active_connections
courier_active_channels

# Histograms
courier_message_delivery_duration_seconds
courier_websocket_message_size_bytes
courier_publish_request_duration_seconds
```

#### Subtask 2.1.2: Prometheus Endpoint

**Files to modify:**
```
courier/
├── src/courier/presentation/api/metrics.py    # NEW
├── src/courier/main.py                        # Add route
```

**Implementation:**
- [ ] Create `/metrics` endpoint
- [ ] Expose Prometheus metrics
- [ ] Add PrometheusMiddleware to FastAPI

**Acceptance Criteria:**
- [ ] `/metrics` endpoint returns Prometheus format
- [ ] All key metrics are tracked
- [ ] Metrics update in real-time
- [ ] No performance degradation

**Testing:**
- [ ] Test metrics endpoint
- [ ] Verify metric values are correct
- [ ] Load test with metrics enabled

---

### Task 2.2: Enhanced Health Checks

**Status:** Partially complete  
**Time:** 1 day  
**Priority:** MEDIUM

**Objective:** Comprehensive health reporting

#### Subtask 2.2.1: Detailed Health Check

**Files to modify:**
```
courier/
├── src/courier/presentation/api/health.py
```

**Implementation:**
- [ ] Add Redis connectivity check (if using Redis in Phase 4)
- [ ] Add memory usage check
- [ ] Add connection pool status
- [ ] Add recent error rate
- [ ] Return detailed status per component

**Response format:**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-28T12:00:00Z",
  "uptime": 86400,
  "version": "1.0.0",
  "components": {
    "websocket_server": {
      "status": "healthy",
      "active_connections": 142,
      "active_channels": 38
    },
    "redis": {
      "status": "healthy",
      "latency_ms": 2.3
    },
    "memory": {
      "status": "healthy",
      "usage_mb": 156,
      "limit_mb": 512
    }
  }
}
```

**Acceptance Criteria:**
- [ ] Health check includes all components
- [ ] Returns 200 when healthy, 503 when unhealthy
- [ ] Includes actionable information
- [ ] Fast response (<50ms)

**Testing:**
- [ ] Test healthy state
- [ ] Test degraded state
- [ ] Test unhealthy state

---

### Task 2.3: Structured Logging

**Status:** Partially complete  
**Time:** 1 day  
**Priority:** MEDIUM

**Objective:** JSON structured logs for production

#### Subtask 2.3.1: Logging Configuration

**Files to modify:**
```
courier/
├── src/courier/config/logging.py    # NEW
├── src/courier/main.py              # Update logging setup
```

**Implementation:**
- [ ] JSON formatter for production
- [ ] Human-readable formatter for development
- [ ] Log levels by environment
- [ ] Request ID tracking
- [ ] Correlation ID propagation

**Log format:**
```json
{
  "timestamp": "2025-10-28T12:00:00.123Z",
  "level": "INFO",
  "logger": "courier.websocket",
  "message": "WebSocket client connected",
  "context": {
    "user_id": "user_123",
    "channel": "user.123",
    "connection_id": "conn_abc"
  },
  "request_id": "req_xyz"
}
```

**Acceptance Criteria:**
- [ ] All logs are structured JSON in production
- [ ] Request IDs tracked across logs
- [ ] No sensitive data in logs
- [ ] Log levels configurable

**Testing:**
- [ ] Verify JSON format in production
- [ ] Verify human format in development
- [ ] Test log filtering

---

### Task 2.4: Error Tracking

**Status:** Not started  
**Time:** 1 day  
**Priority:** MEDIUM

**Objective:** Capture and report errors

#### Subtask 2.4.1: Error Handler Middleware

**Files to create:**
```
courier/
├── src/courier/presentation/middleware/
│   └── error_handler.py
```

**Implementation:**
- [ ] Global exception handler
- [ ] Capture unhandled exceptions
- [ ] Log with full context
- [ ] Return appropriate HTTP status
- [ ] Track error metrics

**Acceptance Criteria:**
- [ ] All errors are logged with context
- [ ] Errors tracked in Prometheus
- [ ] User-friendly error messages
- [ ] No stack traces to clients in production

**Testing:**
- [ ] Test various error scenarios
- [ ] Verify error logging
- [ ] Verify metrics updated

---

## 📋 Phase 3: Service Integration (Week 3)

**Priority:** HIGH  
**Goal:** Connect all services to Courier

### Task 3.1: Python Client Library

**Status:** Not started  
**Time:** 2 days  
**Priority:** HIGH

**Objective:** Reusable Python client for backend services

#### Subtask 3.1.1: Create Client Package

**Files to create:**
```
courier-client/
├── pyproject.toml
├── src/
│   └── courier_client/
│       ├── __init__.py
│       ├── client.py
│       ├── events.py          # Event builders
│       └── exceptions.py
└── tests/
    └── test_client.py
```

**Implementation:**
- [ ] Async HTTP client for publishing
- [ ] Event builder helpers
- [ ] Automatic retry logic
- [ ] Type hints and Pydantic models
- [ ] Error handling

**Client API:**
```python
from courier_client import CourierClient

client = CourierClient(
    base_url="http://localhost:8766",
    service_name="prophet"
)

# Publish event
await client.publish(
    channel="user.123",
    event_type="strategy.generation.started",
    data={"strategy_id": "strat_abc"}
)
```

**Acceptance Criteria:**
- [ ] Client supports all event types
- [ ] Type-safe API
- [ ] Automatic retries on failure
- [ ] Published to private PyPI
- [ ] Full documentation

**Testing:**
- [ ] Unit tests for client
- [ ] Integration tests with Courier
- [ ] Test retry logic

---

### Task 3.2: TypeScript Client Library

**Status:** Not started  
**Time:** 2 days  
**Priority:** HIGH

**Objective:** WebSocket client for frontend

#### Subtask 3.2.1: Create TypeScript Package

**Files to create:**
```
packages/courier-client/
├── package.json
├── tsconfig.json
├── src/
│   ├── index.ts
│   ├── client.ts
│   ├── events.ts
│   └── types.ts
└── tests/
    └── client.test.ts
```

**Implementation:**
- [ ] WebSocket connection management
- [ ] Automatic reconnection
- [ ] Event type definitions
- [ ] React hooks (optional)
- [ ] JWT token handling

**Client API:**
```typescript
import { CourierClient } from '@lumiere/courier-client'

const client = new CourierClient({
  url: 'ws://localhost:8766',
  token: getAuthToken()
})

await client.connect()

client.subscribe('backtest.abc', (event) => {
  console.log('Backtest event:', event)
})
```

**Acceptance Criteria:**
- [ ] Type-safe event handling
- [ ] Automatic reconnection
- [ ] Token refresh handling
- [ ] React hooks available
- [ ] Full documentation

**Testing:**
- [ ] Unit tests for client
- [ ] Integration tests with Courier
- [ ] Test reconnection logic

---

### Task 3.3: Prophet Integration

**Status:** Not started  
**Time:** 1 day  
**Priority:** HIGH

**Objective:** Prophet publishes strategy generation events

#### Subtask 3.3.1: Install Courier Client
```bash
cd ~/lumiere/lumiere-backend/prophet
pip install courier-client --index-url http://localhost:9001/simple/
```

#### Subtask 3.3.2: Integrate in Prophet

**Files to modify:**
```
prophet/
├── src/prophet/application/use_cases/generate_strategy.py
```

**Events to publish:**
1. `strategy.generation.started` - When generation begins
2. `strategy.generation.progress` - During generation
3. `strategy.generation.completed` - When complete
4. `strategy.generation.failed` - On error

**Acceptance Criteria:**
- [ ] Events published at correct stages
- [ ] Events include all required data
- [ ] Errors are handled gracefully
- [ ] No performance impact

**Testing:**
- [ ] Test event publishing
- [ ] Verify events received in Courier
- [ ] Test error scenarios

---

### Task 3.4: Cartographe Integration

**Status:** Not started  
**Time:** 1 day  
**Priority:** HIGH

**Objective:** Cartographe publishes backtest events

**Implementation:** Similar to Prophet integration

**Events to publish:**
1. `backtest.started`
2. `backtest.progress`
3. `backtest.completed`
4. `backtest.failed`

---

### Task 3.5: Chevalier Integration

**Status:** Not started  
**Time:** 1 day  
**Priority:** HIGH

**Objective:** Chevalier publishes trade execution events

**Events to publish:**
1. `trade.executed`
2. `order.placed`
3. `order.filled`
4. `order.cancelled`
5. `position.updated`

---

### Task 3.6: Frontend Integration

**Status:** Not started  
**Time:** 2 days  
**Priority:** HIGH

**Objective:** Frontend displays real-time events

#### Subtask 3.6.1: Install TypeScript Client
```bash
cd ~/lumiere/lumiere-frontend
npm install @lumiere/courier-client
```

#### Subtask 3.6.2: Create React Hooks

**Files to create:**
```
frontend/
├── src/hooks/
│   ├── useCourierConnection.ts
│   ├── useBacktestEvents.ts
│   └── useStrategyEvents.ts
```

**Implementation:**
- [ ] `useCourierConnection()` - Manage WebSocket
- [ ] `useBacktestEvents(backtestId)` - Subscribe to backtest
- [ ] `useStrategyEvents(strategyId)` - Subscribe to strategy

**Acceptance Criteria:**
- [ ] Events display in real-time
- [ ] Connection status visible to user
- [ ] Automatic reconnection works
- [ ] No memory leaks

**Testing:**
- [ ] Test event display
- [ ] Test reconnection
- [ ] Test multiple subscriptions

---

## 📋 Phase 4: Scaling & Advanced Features (Week 4) - OPTIONAL

**Priority:** LOW  
**Goal:** Multi-instance support and advanced features

### Task 4.1: Redis Pub/Sub (Optional)

**Status:** Not started  
**Time:** 3 days  
**Priority:** LOW

**Objective:** Enable horizontal scaling

**Implementation:**
- [ ] Add Redis as message broker
- [ ] Publish to Redis instead of in-memory
- [ ] Subscribe to Redis channels
- [ ] Handle multiple Courier instances

**Note:** Only needed if >10,000 concurrent users

---

### Task 4.2: Event Persistence & Replay (Optional)

**Status:** Not started  
**Time:** 2 days  
**Priority:** LOW

**Objective:** Store events for replay

**Implementation:**
- [ ] Store events in PostgreSQL
- [ ] Replay API endpoint
- [ ] Event retention policy (7 days)

**Note:** Only if services require event replay

---

### Task 4.3: Admin Dashboard (Optional)

**Status:** Not started  
**Time:** 2 days  
**Priority:** LOW

**Objective:** Web UI for monitoring

**Implementation:**
- [ ] React admin dashboard
- [ ] Real-time connection view
- [ ] Event stream monitoring
- [ ] Manual event publishing

---

## 📊 Progress Tracking

### Week 1: MVP Security & Validation
- [ ] Task 1.1: Complete WebSocket Auth (1 day)
- [ ] Task 1.2: Event Schema Validation (2 days)
- [ ] Task 1.3: Rate Limiting (1 day)
- [ ] Task 1.4: Graceful Shutdown (1 day)
- [ ] Testing & bug fixes (2 days)

### Week 2: Production Hardening
- [ ] Task 2.1: Prometheus Metrics (2 days)
- [ ] Task 2.2: Enhanced Health Checks (1 day)
- [ ] Task 2.3: Structured Logging (1 day)
- [ ] Task 2.4: Error Tracking (1 day)
- [ ] Testing & documentation (2 days)

### Week 3: Service Integration
- [ ] Task 3.1: Python Client Library (2 days)
- [ ] Task 3.2: TypeScript Client Library (2 days)
- [ ] Task 3.3-3.6: Service Integrations (3 days)

### Week 4: Optional Features
- [ ] Redis Pub/Sub (if needed)
- [ ] Event Persistence (if needed)
- [ ] Admin Dashboard (if wanted)
- [ ] Load testing & optimization

---

## 🎯 Success Criteria

### Phase 1 (MVP) - MUST HAVE
- [ ] WebSocket connections require authentication ✅
- [ ] Invalid events are rejected
- [ ] Rate limiting prevents abuse
- [ ] Graceful shutdown works
- [ ] All tests passing

### Phase 2 (Production) - MUST HAVE
- [ ] Metrics exported to Prometheus
- [ ] Health checks comprehensive
- [ ] Structured logging in place
- [ ] Errors tracked properly

### Phase 3 (Integration) - MUST HAVE
- [ ] Python client library works
- [ ] TypeScript client library works
- [ ] Prophet publishes events
- [ ] Cartographe publishes events
- [ ] Chevalier publishes events
- [ ] Frontend displays events

### Phase 4 (Scale) - OPTIONAL
- [ ] Redis pub/sub working (if implemented)
- [ ] Event replay functional (if implemented)
- [ ] Admin dashboard accessible (if implemented)

---

## 🚀 Next Actions

1. **IMMEDIATE:** Implement Event Schema Validation (Task 1.2)
   - Start with base event schema
   - Create Prophet event schemas
   - Integrate validation in publish endpoint

2. **THIS WEEK:** Complete Phase 1
   - Event schemas
   - Rate limiting
   - Graceful shutdown

3. **NEXT WEEK:** Phase 2 - Production hardening

---

**END OF TODO DOCUMENT**

**Version:** 1.0  
**Last Updated:** October 28, 2025  
**Current Phase:** Phase 1 - Task 1.2 (Event Schema Validation)

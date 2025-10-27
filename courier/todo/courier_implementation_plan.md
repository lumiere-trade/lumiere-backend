# Courier Implementation Plan
## Complete Roadmap from Current State to Production-Ready Event Bus

**Version:** 1.0  
**Date:** October 26, 2025  
**Target Completion:** 4 weeks  
**Status:** Planning Phase

---

## Table of Contents

1. [Current State Analysis](#1-current-state-analysis)
2. [Phase 1: MVP Security & Validation](#2-phase-1-mvp-security--validation)
3. [Phase 2: Production Hardening](#3-phase-2-production-hardening)
4. [Phase 3: Service Integration](#4-phase-3-service-integration)
5. [Phase 4: Scaling & Advanced Features](#5-phase-4-scaling--advanced-features)
6. [Testing Strategy](#6-testing-strategy)
7. [Deployment Plan](#7-deployment-plan)
8. [Rollback Procedures](#8-rollback-procedures)

---

## 1. Current State Analysis

### 1.1 What Exists (According to HLD v1.2)

**Core Features:**
- ✅ FastAPI WebSocket server
- ✅ Channel-based routing (`global`, `user.*`, `strategy.*`, `forge.job.*`)
- ✅ Dynamic channel creation
- ✅ HTTP publish endpoints (POST /publish, POST /publish/{channel})
- ✅ WebSocket endpoint (WS /ws/{channel})
- ✅ Connection management (heartbeat, cleanup)
- ✅ Health check (GET /health)
- ✅ Statistics (GET /stats)

**Architecture:**
- ✅ In-process pub/sub (no external dependencies)
- ✅ Stateless broker (no persistence)
- ✅ systemd service deployment

### 1.2 Critical Gaps

**Security:**
- ❌ No WebSocket authentication
- ❌ No authorization checks
- ❌ No rate limiting

**Data Quality:**
- ❌ No event schema validation
- ❌ No payload size limits
- ❌ No malformed data protection

**Production Readiness:**
- ❌ No graceful shutdown
- ❌ No metrics/monitoring
- ❌ No event persistence
- ❌ No replay capability

**Integration:**
- ❌ Services not publishing events
- ❌ Frontend not consuming events
- ❌ No client libraries

---

## 2. Phase 1: MVP Security & Validation

**Duration:** 1 week  
**Goal:** Make Courier secure and validate data integrity  
**Priority:** CRITICAL - Cannot deploy without this

### 2.1 Task Breakdown

#### Task 1.1: WebSocket Authentication (2 days)

**Objective:** Verify JWT tokens and authorize channel access

**Files to Create/Modify:**
```
courier/
├── src/courier/
│   ├── domain/
│   │   └── auth.py                    # NEW: Auth domain models
│   ├── infrastructure/
│   │   └── jwt_verifier.py            # NEW: JWT verification
│   └── api/
│       └── websocket.py               # MODIFY: Add auth
```

**Implementation:**

**Step 1:** Create auth domain models
```python
# courier/src/courier/domain/auth.py

from pydantic import BaseModel
from typing import Optional

class TokenPayload(BaseModel):
    user_id: str
    wallet_address: str
    exp: int
    iat: int

class AuthenticatedClient(BaseModel):
    user_id: str
    wallet_address: str
    channel: str
    connected_at: str
```

**Step 2:** Create JWT verifier
```python
# courier/src/courier/infrastructure/jwt_verifier.py

import jwt
from datetime import datetime
from courier.domain.auth import TokenPayload
from courier.config.settings import settings

class JWTVerifier:
    def __init__(self, secret: str, algorithm: str = "HS256"):
        self.secret = secret
        self.algorithm = algorithm
    
    def verify_token(self, token: str) -> TokenPayload:
        """Verify JWT token and return payload"""
        try:
            payload = jwt.decode(
                token,
                self.secret,
                algorithms=[self.algorithm]
            )
            return TokenPayload(**payload)
        except jwt.ExpiredSignatureError:
            raise ValueError("Token expired")
        except jwt.InvalidTokenError:
            raise ValueError("Invalid token")
    
    def verify_channel_access(
        self, 
        user_id: str, 
        channel: str
    ) -> bool:
        """Verify user can access channel"""
        
        # Global channel - everyone can read
        if channel == "global":
            return True
        
        # User channel - must match user_id
        if channel.startswith("user."):
            channel_user_id = channel.split(".")[1]
            return channel_user_id == user_id
        
        # Strategy channel - check ownership in database
        if channel.startswith("strategy."):
            # TODO: Query Architect to verify strategy ownership
            return True
        
        # Backtest channel - ephemeral, assume authorized
        if channel.startswith("backtest."):
            return True
        
        # Forge job channel - ephemeral, assume authorized
        if channel.startswith("forge.job."):
            return True
        
        return False
```

**Step 3:** Modify WebSocket endpoint
```python
# courier/src/courier/api/websocket.py

from fastapi import WebSocket, WebSocketDisconnect, Query, status
from typing import Optional
from courier.infrastructure.jwt_verifier import JWTVerifier
from courier.config.settings import settings

jwt_verifier = JWTVerifier(secret=settings.JWT_SECRET)

@router.websocket("/ws/{channel}")
async def websocket_endpoint(
    websocket: WebSocket,
    channel: str,
    token: Optional[str] = Query(None)
):
    """WebSocket endpoint with authentication"""
    
    # Verify token presence
    if not token:
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Authentication token required"
        )
        return
    
    # Verify token validity
    try:
        token_payload = jwt_verifier.verify_token(token)
    except ValueError as e:
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION,
            reason=str(e)
        )
        return
    
    # Verify channel access
    if not jwt_verifier.verify_channel_access(token_payload.user_id, channel):
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Unauthorized access to channel"
        )
        return
    
    # Accept connection
    await websocket.accept()
    
    reporter.info(
        "WebSocket client connected",
        context="WebSocket",
        channel=channel,
        user_id=token_payload.user_id,
        verbose_level=2
    )
    
    # Register client with user_id
    await broker.subscribe(
        channel, 
        websocket,
        user_id=token_payload.user_id
    )
    
    try:
        # Heartbeat loop
        while True:
            try:
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0
                )
                # Handle ping/pong
                if data == "ping":
                    await websocket.send_text("pong")
            except asyncio.TimeoutError:
                # Send ping
                await websocket.send_text("ping")
    
    except WebSocketDisconnect:
        reporter.info(
            "WebSocket client disconnected",
            context="WebSocket",
            channel=channel,
            user_id=token_payload.user_id,
            verbose_level=2
        )
        await broker.unsubscribe(channel, websocket)
```

**Step 4:** Update settings
```python
# courier/src/courier/config/settings.py

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Existing settings...
    
    # JWT Authentication
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    
    class Config:
        env_file = ".env"

settings = Settings()
```

**Step 5:** Update environment files
```bash
# courier/config/production.yaml
jwt:
  secret: ${JWT_SECRET}  # From environment
  algorithm: "HS256"

# courier/config/development.yaml
jwt:
  secret: "dev-secret-change-in-production"
  algorithm: "HS256"
```

**Acceptance Criteria:**
- [ ] WebSocket connection requires valid JWT token
- [ ] Token expiration is enforced
- [ ] User can only access authorized channels
- [ ] Unauthorized access returns 1008 policy violation
- [ ] User ID is logged with all connections

---

#### Task 1.2: Event Schema Validation (2 days)

**Objective:** Validate all published events against schema

**Files to Create/Modify:**
```
courier/
├── src/courier/
│   ├── domain/
│   │   ├── events/
│   │   │   ├── __init__.py
│   │   │   ├── base.py               # NEW: Base event
│   │   │   ├── prophet.py            # NEW: Prophet events
│   │   │   ├── backtest.py           # NEW: Backtest events
│   │   │   ├── trading.py            # NEW: Trading events
│   │   │   └── system.py             # NEW: System events
│   └── api/
│       └── publish.py                # MODIFY: Add validation
```

**Implementation:**

**Step 1:** Create base event
```python
# courier/src/courier/domain/events/base.py

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class BaseEvent(BaseModel):
    """Base event that all events must inherit from"""
    
    type: str = Field(..., description="Event type")
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat() + "Z",
        description="ISO 8601 timestamp"
    )
    source: str = Field(..., description="Publishing service")
    trace_id: Optional[str] = Field(None, description="Correlation ID")
    
    class Config:
        json_schema_extra = {
            "example": {
                "type": "event.action",
                "timestamp": "2025-10-26T10:00:00.000Z",
                "source": "service_name",
                "trace_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        }
```

**Step 2:** Create Prophet events
```python
# courier/src/courier/domain/events/prophet.py

from typing import Literal, Dict, List
from pydantic import Field
from .base import BaseEvent

class ProphetMessageChunk(BaseEvent):
    type: Literal["prophet.message_chunk"]
    conversation_id: str
    chunk: str
    is_final: bool

class ProphetTSDLReady(BaseEvent):
    type: Literal["prophet.tsdl_ready"]
    conversation_id: str
    tsdl: str
    metadata: Dict[str, any] = Field(
        ...,
        description="Strategy metadata"
    )

class ProphetError(BaseEvent):
    type: Literal["prophet.error"]
    conversation_id: str
    error_code: str
    message: str
    details: str = Field(default="")

# Union type
ProphetEvent = (
    ProphetMessageChunk | 
    ProphetTSDLReady | 
    ProphetError
)
```

**Step 3:** Create Backtest events
```python
# courier/src/courier/domain/events/backtest.py

from typing import Literal, Dict
from pydantic import Field, field_validator
from .base import BaseEvent

class BacktestStarted(BaseEvent):
    type: Literal["backtest.started"]
    backtest_id: str
    job_id: str
    user_id: str
    parameters: Dict[str, any]

class BacktestProgress(BaseEvent):
    type: Literal["backtest.progress"]
    backtest_id: str
    job_id: str
    user_id: str
    progress: float = Field(..., ge=0.0, le=1.0)
    stage: str
    message: str
    
    @field_validator('progress')
    def validate_progress(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Progress must be between 0.0 and 1.0')
        return v

class BacktestCompleted(BaseEvent):
    type: Literal["backtest.completed"]
    backtest_id: str
    job_id: str
    user_id: str
    duration_seconds: int
    summary: Dict[str, any]

class BacktestFailed(BaseEvent):
    type: Literal["backtest.failed"]
    backtest_id: str
    job_id: str
    user_id: str
    error_code: str
    message: str
    details: str = Field(default="")

class BacktestCancelled(BaseEvent):
    type: Literal["backtest.cancelled"]
    backtest_id: str
    job_id: str
    user_id: str
    reason: str
    progress_at_cancellation: float

# Union type
BacktestEvent = (
    BacktestStarted |
    BacktestProgress |
    BacktestCompleted |
    BacktestFailed |
    BacktestCancelled
)
```

**Step 4:** Create Trading events
```python
# courier/src/courier/domain/events/trading.py

from typing import Literal
from pydantic import Field
from .base import BaseEvent

class StrategyDeployed(BaseEvent):
    type: Literal["strategy.deployed"]
    strategy_id: str
    user_id: str
    name: str
    initial_capital: float
    token_pair: str
    status: Literal["active"]

class TradeSignalGenerated(BaseEvent):
    type: Literal["trade.signal_generated"]
    strategy_id: str
    user_id: str
    signal_id: str
    token: str
    direction: Literal["buy", "sell"]
    confidence: float = Field(..., ge=0.0, le=1.0)
    reason: str
    price_at_signal: float

class TradeOrderFilled(BaseEvent):
    type: Literal["trade.order_filled"]
    strategy_id: str
    user_id: str
    order_id: str
    token: str
    direction: Literal["buy", "sell"]
    fill_price: float
    fill_amount: float
    total_value: float
    fees: float
    tx_signature: str

class PositionClosed(BaseEvent):
    type: Literal["position.closed"]
    strategy_id: str
    user_id: str
    position_id: str
    token: str
    entry_price: float
    exit_price: float
    size: float
    realized_pnl: float
    realized_pnl_percentage: float
    reason: Literal["take_profit", "stop_loss", "manual", "signal"]
    tx_signature: str

# Union type
TradingEvent = (
    StrategyDeployed |
    TradeSignalGenerated |
    TradeOrderFilled |
    PositionClosed
    # ... add all 12 trading events
)
```

**Step 5:** Create master event union
```python
# courier/src/courier/domain/events/__init__.py

from typing import Union
from .prophet import ProphetEvent
from .backtest import BacktestEvent
from .trading import TradingEvent
from .system import SystemEvent

# Master union type for all events
CourierEvent = Union[
    ProphetEvent,
    BacktestEvent,
    TradingEvent,
    SystemEvent
]

# Export all event types
__all__ = [
    "CourierEvent",
    "ProphetEvent",
    "BacktestEvent",
    "TradingEvent",
    "SystemEvent"
]
```

**Step 6:** Update publish endpoint
```python
# courier/src/courier/api/publish.py

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel, ValidationError
from typing import Dict, Any
from courier.domain.events import CourierEvent

router = APIRouter()

class PublishRequest(BaseModel):
    channel: str
    data: Dict[str, Any]

@router.post("/publish")
async def publish_event(
    request: PublishRequest,
    x_service_name: str = Header(..., alias="X-Service-Name")
):
    """
    Publish event to channel with schema validation
    
    Headers:
        X-Service-Name: Name of publishing service
    """
    
    # Validate event schema
    try:
        # Pydantic will validate against CourierEvent union
        validated_event = CourierEvent.model_validate(request.data)
    except ValidationError as e:
        reporter.error(
            "Event schema validation failed",
            context="Publish",
            channel=request.channel,
            service=x_service_name,
            errors=e.errors(),
            verbose_level=1
        )
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Invalid event schema",
                "validation_errors": e.errors()
            }
        )
    
    # Verify source matches header
    if validated_event.source != x_service_name:
        raise HTTPException(
            status_code=400,
            detail="Event source must match X-Service-Name header"
        )
    
    # Publish to broker
    clients_reached = await broker.publish(
        request.channel,
        validated_event.model_dump()
    )
    
    reporter.info(
        "Event published",
        context="Publish",
        channel=request.channel,
        event_type=validated_event.type,
        clients_reached=clients_reached,
        verbose_level=2
    )
    
    return {
        "status": "published",
        "channel": request.channel,
        "event_type": validated_event.type,
        "clients_reached": clients_reached,
        "timestamp": validated_event.timestamp
    }
```

**Acceptance Criteria:**
- [ ] All event types have Pydantic models
- [ ] Invalid events are rejected with 400
- [ ] Validation errors are descriptive
- [ ] Event source matches service header
- [ ] All fields are validated (types, ranges, enums)

---

#### Task 1.3: Rate Limiting (1 day)

**Objective:** Prevent abuse of publish endpoint

**Files to Create:**
```
courier/
├── src/courier/
│   ├── infrastructure/
│   │   └── rate_limiter.py           # NEW
│   └── api/
│       └── publish.py                # MODIFY
```

**Implementation:**

```python
# courier/src/courier/infrastructure/rate_limiter.py

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List

class RateLimiter:
    """
    Simple in-memory rate limiter using sliding window
    
    For production with multiple instances, use Redis
    """
    
    def __init__(
        self,
        limit: int = 100,
        window_seconds: int = 60
    ):
        self.limit = limit
        self.window = timedelta(seconds=window_seconds)
        self.requests: Dict[str, List[datetime]] = defaultdict(list)
    
    async def check_rate_limit(self, identifier: str) -> bool:
        """
        Check if identifier is within rate limit
        
        Returns:
            True if allowed, False if rate limit exceeded
        """
        now = datetime.utcnow()
        cutoff = now - self.window
        
        # Remove expired timestamps
        self.requests[identifier] = [
            ts for ts in self.requests[identifier]
            if ts > cutoff
        ]
        
        # Check limit
        if len(self.requests[identifier]) >= self.limit:
            return False
        
        # Add current request
        self.requests[identifier].append(now)
        return True
    
    def get_remaining(self, identifier: str) -> int:
        """Get remaining requests in current window"""
        return max(0, self.limit - len(self.requests[identifier]))
    
    def get_reset_time(self, identifier: str) -> datetime:
        """Get time when rate limit resets"""
        if not self.requests[identifier]:
            return datetime.utcnow()
        
        oldest = min(self.requests[identifier])
        return oldest + self.window
```

**Usage in publish endpoint:**
```python
# courier/src/courier/api/publish.py

from courier.infrastructure.rate_limiter import RateLimiter

# Initialize rate limiter
# 100 requests per minute per service
rate_limiter = RateLimiter(limit=100, window_seconds=60)

@router.post("/publish")
async def publish_event(
    request: PublishRequest,
    x_service_name: str = Header(..., alias="X-Service-Name")
):
    """Publish event with rate limiting"""
    
    # Check rate limit
    if not await rate_limiter.check_rate_limit(x_service_name):
        remaining = rate_limiter.get_remaining(x_service_name)
        reset_time = rate_limiter.get_reset_time(x_service_name)
        
        reporter.warning(
            "Rate limit exceeded",
            context="Publish",
            service=x_service_name,
            remaining=remaining,
            verbose_level=1
        )
        
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Rate limit exceeded",
                "limit": rate_limiter.limit,
                "window_seconds": rate_limiter.window.total_seconds(),
                "remaining": remaining,
                "reset_at": reset_time.isoformat() + "Z"
            }
        )
    
    # ... rest of publish logic ...
```

**Acceptance Criteria:**
- [ ] Services limited to 100 requests/minute
- [ ] Rate limit per service (not global)
- [ ] 429 response with reset time
- [ ] Headers show remaining requests

---

#### Task 1.4: Graceful Shutdown (1 day)

**Objective:** Close connections cleanly on shutdown

**Files to Modify:**
```
courier/
└── src/courier/
    └── main.py                        # MODIFY
```

**Implementation:**

```python
# courier/src/courier/main.py

import signal
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager
    Handles startup and shutdown logic
    """
    
    # Startup
    reporter.info(
        "Courier starting up",
        context="Lifecycle",
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
        verbose_level=1
    )
    
    # Setup shutdown event
    shutdown_event = asyncio.Event()
    
    def handle_shutdown(signum, frame):
        """Handle shutdown signals"""
        reporter.info(
            "Shutdown signal received",
            context="Lifecycle",
            signal=signal.Signals(signum).name,
            verbose_level=1
        )
        shutdown_event.set()
    
    # Register signal handlers
    signal.signal(signal.SIGTERM, handle_shutdown)
    signal.signal(signal.SIGINT, handle_shutdown)
    
    yield
    
    # Shutdown
    reporter.info(
        "Courier shutting down",
        context="Lifecycle",
        verbose_level=1
    )
    
    # Close all WebSocket connections gracefully
    await broker.close_all_connections(
        reason="Server shutting down for maintenance"
    )
    
    reporter.info(
        "All connections closed",
        context="Lifecycle",
        verbose_level=1
    )
    
    # Wait a moment for final cleanup
    await asyncio.sleep(1)
    
    reporter.info(
        "Courier shutdown complete",
        context="Lifecycle",
        verbose_level=1
    )

# Create app with lifespan
app = FastAPI(
    title="Courier Event Bus",
    version=settings.VERSION,
    lifespan=lifespan
)
```

**Update broker to support graceful shutdown:**
```python
# courier/src/courier/core/broker.py

class EventBroker:
    async def close_all_connections(self, reason: str = "Server shutdown"):
        """Close all WebSocket connections gracefully"""
        
        reporter.info(
            "Closing all WebSocket connections",
            context="Broker",
            total_connections=len(self.get_all_clients()),
            verbose_level=1
        )
        
        close_tasks = []
        
        for channel, clients in self.clients.items():
            for websocket in clients:
                close_tasks.append(
                    websocket.close(
                        code=status.WS_1001_GOING_AWAY,
                        reason=reason
                    )
                )
        
        # Close all connections concurrently
        await asyncio.gather(*close_tasks, return_exceptions=True)
        
        # Clear client registry
        self.clients.clear()
        self.client_metadata.clear()
        
        reporter.info(
            "All connections closed",
            context="Broker",
            verbose_level=1
        )
```

**Acceptance Criteria:**
- [ ] SIGTERM triggers graceful shutdown
- [ ] SIGINT (Ctrl+C) triggers graceful shutdown
- [ ] All WebSocket connections close with 1001 code
- [ ] Shutdown reason sent to clients
- [ ] No errors during shutdown

---

### 2.2 Phase 1 Testing

**Create integration tests:**
```python
# courier/tests/integration/test_auth.py

import pytest
from fastapi.testclient import TestClient
import jwt

def test_websocket_requires_token(client: TestClient):
    """WebSocket connection must provide token"""
    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect("/ws/user.123"):
            pass
    assert exc.value.code == 1008

def test_websocket_rejects_invalid_token(client: TestClient):
    """Invalid token is rejected"""
    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect("/ws/user.123?token=invalid"):
            pass
    assert exc.value.code == 1008

def test_websocket_rejects_unauthorized_channel(client: TestClient):
    """User cannot access other user's channel"""
    token = create_test_token(user_id="user_123")
    
    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect(f"/ws/user.456?token={token}"):
            pass
    assert exc.value.code == 1008

def test_websocket_accepts_valid_token(client: TestClient):
    """Valid token allows connection"""
    token = create_test_token(user_id="user_123")
    
    with client.websocket_connect(f"/ws/user.123?token={token}") as ws:
        ws.send_text("ping")
        data = ws.receive_text()
        assert data == "pong"
```

```python
# courier/tests/integration/test_validation.py

def test_publish_validates_event_schema(client: TestClient):
    """Invalid event schema is rejected"""
    response = client.post(
        "/publish",
        json={
            "channel": "user.123",
            "data": {
                "type": "invalid.event",
                "invalid_field": "value"
            }
        },
        headers={"X-Service-Name": "test"}
    )
    assert response.status_code == 400
    assert "validation_errors" in response.json()["detail"]

def test_publish_accepts_valid_event(client: TestClient):
    """Valid event is accepted"""
    response = client.post(
        "/publish",
        json={
            "channel": "user.123",
            "data": {
                "type": "backtest.started",
                "source": "test",
                "backtest_id": "bt_123",
                "job_id": "job_xyz",
                "user_id": "user_123",
                "parameters": {
                    "timeframe": {"start": "2024-01-01", "end": "2024-12-31"},
                    "initial_capital": 10000,
                    "token_pair": "SOL/USDC"
                }
            }
        },
        headers={"X-Service-Name": "test"}
    )
    assert response.status_code == 200
```

```python
# courier/tests/integration/test_rate_limiting.py

def test_rate_limit_enforced(client: TestClient):
    """Rate limit is enforced"""
    
    # Make 100 requests (limit)
    for i in range(100):
        response = client.post(
            "/publish",
            json=create_valid_event(),
            headers={"X-Service-Name": "test"}
        )
        assert response.status_code == 200
    
    # 101st request should be rate limited
    response = client.post(
        "/publish",
        json=create_valid_event(),
        headers={"X-Service-Name": "test"}
    )
    assert response.status_code == 429
    assert "rate limit exceeded" in response.json()["detail"]["error"].lower()
```

### 2.3 Phase 1 Deployment

**Steps:**
1. Create feature branch: `git checkout -b feature/phase-1-security`
2. Implement all tasks
3. Run full test suite: `pytest -v`
4. Update documentation
5. Code review
6. Merge to develop
7. Deploy to development environment
8. Smoke tests
9. Deploy to production

**Rollback Plan:**
- Keep old version running during deployment
- If issues detected, revert systemd service to old version
- Monitor logs for 1 hour after deployment

---

## 3. Phase 2: Production Hardening

**Duration:** 1 week  
**Goal:** Add monitoring, metrics, and operational tools  
**Priority:** HIGH - Needed for production confidence

### 3.1 Task Breakdown

#### Task 2.1: Prometheus Metrics (2 days)

**Objective:** Export metrics for monitoring

**Files to Create:**
```
courier/
├── src/courier/
│   ├── infrastructure/
│   │   └── metrics.py                # NEW
│   └── api/
│       └── metrics.py                # NEW: Metrics endpoint
```

**Implementation:**

```python
# courier/src/courier/infrastructure/metrics.py

from prometheus_client import (
    Counter, 
    Histogram, 
    Gauge, 
    generate_latest,
    CONTENT_TYPE_LATEST
)

# Event metrics
events_published_total = Counter(
    'courier_events_published_total',
    'Total number of events published',
    ['channel', 'event_type', 'source']
)

events_delivered_total = Counter(
    'courier_events_delivered_total',
    'Total number of events delivered to clients',
    ['channel', 'event_type']
)

events_validation_failed_total = Counter(
    'courier_events_validation_failed_total',
    'Total number of events that failed validation',
    ['event_type', 'source']
)

# Connection metrics
websocket_connections_active = Gauge(
    'courier_websocket_connections_active',
    'Current number of active WebSocket connections',
    ['channel']
)

websocket_connections_total = Counter(
    'courier_websocket_connections_total',
    'Total number of WebSocket connections',
    ['channel']
)

websocket_disconnections_total = Counter(
    'courier_websocket_disconnections_total',
    'Total number of WebSocket disconnections',
    ['channel', 'reason']
)

# Performance metrics
publish_latency_seconds = Histogram(
    'courier_publish_latency_seconds',
    'Time taken to publish event',
    ['channel'],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0)
)

websocket_message_latency_seconds = Histogram(
    'courier_websocket_message_latency_seconds',
    'Time taken to deliver message to WebSocket client',
    ['channel'],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0)
)

# Rate limiting metrics
rate_limit_exceeded_total = Counter(
    'courier_rate_limit_exceeded_total',
    'Total number of rate limit violations',
    ['service']
)

# Error metrics
errors_total = Counter(
    'courier_errors_total',
    'Total number of errors',
    ['error_type', 'component']
)
```

**Metrics endpoint:**
```python
# courier/src/courier/api/metrics.py

from fastapi import APIRouter, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from courier.infrastructure.metrics import *

router = APIRouter()

@router.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )
```

**Instrument publish endpoint:**
```python
# courier/src/courier/api/publish.py

from courier.infrastructure.metrics import (
    events_published_total,
    events_validation_failed_total,
    publish_latency_seconds,
    rate_limit_exceeded_total
)

@router.post("/publish")
async def publish_event(request: PublishRequest, ...):
    # Rate limiting
    if not await rate_limiter.check_rate_limit(x_service_name):
        rate_limit_exceeded_total.labels(service=x_service_name).inc()
        raise HTTPException(...)
    
    # Validation
    try:
        validated_event = CourierEvent.model_validate(request.data)
    except ValidationError as e:
        events_validation_failed_total.labels(
            event_type=request.data.get('type', 'unknown'),
            source=x_service_name
        ).inc()
        raise HTTPException(...)
    
    # Publish with timing
    with publish_latency_seconds.labels(channel=request.channel).time():
        clients_reached = await broker.publish(
            request.channel,
            validated_event.model_dump()
        )
    
    # Record metrics
    events_published_total.labels(
        channel=request.channel,
        event_type=validated_event.type,
        source=validated_event.source
    ).inc()
    
    return {...}
```

**Acceptance Criteria:**
- [ ] Metrics exported at /metrics
- [ ] All key operations instrumented
- [ ] Prometheus can scrape metrics
- [ ] Grafana dashboard created

---

#### Task 2.2: Health Check Enhancement (1 day)

**Objective:** More detailed health information

```python
# courier/src/courier/api/health.py

from fastapi import APIRouter
from datetime import datetime
from courier.core.broker import broker

router = APIRouter()

@router.get("/health")
async def health_check():
    """Enhanced health check with component status"""
    
    start_time = broker.start_time or datetime.utcnow()
    uptime_seconds = (datetime.utcnow() - start_time).total_seconds()
    
    # Check components
    components = {
        "broker": "healthy",
        "rate_limiter": "healthy",
        "jwt_verifier": "healthy"
    }
    
    # Overall status
    status = "healthy" if all(
        c == "healthy" for c in components.values()
    ) else "degraded"
    
    return {
        "status": status,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "uptime_seconds": int(uptime_seconds),
        "components": components,
        "metrics": {
            "active_connections": broker.get_connection_count(),
            "active_channels": len(broker.clients),
            "total_messages_sent": broker.total_messages_sent,
            "total_messages_received": broker.total_messages_received
        },
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

@router.get("/health/live")
async def liveness_check():
    """Kubernetes liveness probe"""
    return {"status": "alive"}

@router.get("/health/ready")
async def readiness_check():
    """Kubernetes readiness probe"""
    # Check if service is ready to accept connections
    is_ready = broker.is_initialized()
    
    return {
        "status": "ready" if is_ready else "not_ready",
        "ready": is_ready
    }
```

---

#### Task 2.3: Structured Logging Enhancement (1 day)

**Objective:** Consistent, searchable logs

```python
# courier/src/courier/infrastructure/logging.py

import json
from datetime import datetime
from typing import Dict, Any

class StructuredLogger:
    """
    Structured JSON logging for production
    Compatible with ELK, Loki, CloudWatch
    """
    
    def __init__(self, service_name: str):
        self.service_name = service_name
    
    def _log(
        self, 
        level: str, 
        message: str,
        **kwargs
    ):
        """Emit structured log entry"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": level,
            "service": self.service_name,
            "message": message,
            **kwargs
        }
        
        print(json.dumps(log_entry))
    
    def info(self, message: str, **kwargs):
        self._log("INFO", message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        self._log("WARNING", message, **kwargs)
    
    def error(self, message: str, **kwargs):
        self._log("ERROR", message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        self._log("DEBUG", message, **kwargs)

# Usage
logger = StructuredLogger("courier")

logger.info(
    "Event published",
    channel="user.123",
    event_type="backtest.started",
    clients_reached=2
)
# Output: {"timestamp": "...", "level": "INFO", "service": "courier", 
#          "message": "Event published", "channel": "user.123", ...}
```

---

#### Task 2.4: Error Tracking Integration (1 day)

**Objective:** Capture and track errors (Sentry optional)

```python
# courier/src/courier/infrastructure/error_tracking.py

import sys
import traceback
from typing import Optional, Dict, Any

class ErrorTracker:
    """
    Error tracking and aggregation
    Can integrate with Sentry in production
    """
    
    def __init__(self):
        self.errors: Dict[str, int] = {}
    
    def capture_exception(
        self,
        exception: Exception,
        context: Optional[Dict[str, Any]] = None
    ):
        """Capture exception with context"""
        
        error_type = type(exception).__name__
        error_message = str(exception)
        stack_trace = ''.join(
            traceback.format_exception(*sys.exc_info())
        )
        
        # Count errors
        self.errors[error_type] = self.errors.get(error_type, 0) + 1
        
        # Log structured error
        logger.error(
            f"Exception occurred: {error_message}",
            error_type=error_type,
            error_count=self.errors[error_type],
            stack_trace=stack_trace,
            context=context or {}
        )
        
        # TODO: Send to Sentry if configured
        # if settings.SENTRY_DSN:
        #     sentry_sdk.capture_exception(exception)
    
    def get_error_stats(self) -> Dict[str, int]:
        """Get error statistics"""
        return self.errors.copy()

error_tracker = ErrorTracker()
```

---

### 3.2 Phase 2 Deliverables

**Monitoring:**
- [ ] Prometheus metrics exported
- [ ] Grafana dashboard created
- [ ] Alerts configured (high error rate, low uptime)

**Observability:**
- [ ] Structured JSON logging
- [ ] Error tracking system
- [ ] Enhanced health checks

**Documentation:**
- [ ] Metrics documentation
- [ ] Grafana dashboard screenshots
- [ ] Runbook for common issues

---

## 4. Phase 3: Service Integration

**Duration:** 1 week  
**Goal:** Integrate backend services and frontend  
**Priority:** HIGH - Core functionality

### 4.1 Task Breakdown

#### Task 3.1: Python Client Library (2 days)

**Objective:** Easy integration for backend services

**Create new package:**
```
lumiere-public/
└── courier-client-python/
    ├── pyproject.toml
    ├── src/
    │   └── courier_client/
    │       ├── __init__.py
    │       ├── client.py
    │       └── events.py
    └── tests/
        └── test_client.py
```

**Implementation:**

```python
# courier-client-python/src/courier_client/client.py

import httpx
from datetime import datetime
from typing import Dict, Any, Optional

class CourierClient:
    """
    Python client for publishing events to Courier
    
    Usage:
        courier = CourierClient(
            url="http://courier:8766",
            service_name="prophet"
        )
        
        await courier.publish(
            channel="user.123",
            event_type="prophet.tsdl_ready",
            data={
                "conversation_id": "conv_abc",
                "tsdl": "...",
                "metadata": {...}
            }
        )
    """
    
    def __init__(
        self,
        url: str,
        service_name: str,
        timeout: float = 5.0
    ):
        self.url = url.rstrip('/')
        self.service_name = service_name
        self.client = httpx.AsyncClient(timeout=timeout)
    
    async def publish(
        self,
        channel: str,
        event_type: str,
        data: Dict[str, Any],
        trace_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Publish event to Courier
        
        Args:
            channel: Target channel (e.g., "user.123")
            event_type: Event type (e.g., "backtest.started")
            data: Event-specific data
            trace_id: Optional correlation ID
        
        Returns:
            Response from Courier
        
        Raises:
            httpx.HTTPStatusError: If publish fails
        """
        
        payload = {
            "channel": channel,
            "data": {
                "type": event_type,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "source": self.service_name,
                **({"trace_id": trace_id} if trace_id else {}),
                **data
            }
        }
        
        response = await self.client.post(
            f"{self.url}/publish",
            json=payload,
            headers={"X-Service-Name": self.service_name}
        )
        
        response.raise_for_status()
        return response.json()
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
```

**Helper functions:**
```python
# courier-client-python/src/courier_client/events.py

from typing import Dict, Any

def backtest_started(
    backtest_id: str,
    job_id: str,
    user_id: str,
    parameters: Dict[str, Any]
) -> tuple[str, str, Dict[str, Any]]:
    """
    Helper to create backtest.started event
    
    Returns: (channel, event_type, data)
    """
    return (
        f"user.{user_id}",
        "backtest.started",
        {
            "backtest_id": backtest_id,
            "job_id": job_id,
            "user_id": user_id,
            "parameters": parameters
        }
    )

def backtest_progress(
    backtest_id: str,
    job_id: str,
    user_id: str,
    progress: float,
    stage: str,
    message: str
) -> tuple[str, str, Dict[str, Any]]:
    """Helper to create backtest.progress event"""
    return (
        f"user.{user_id}",
        "backtest.progress",
        {
            "backtest_id": backtest_id,
            "job_id": job_id,
            "user_id": user_id,
            "progress": progress,
            "stage": stage,
            "message": message
        }
    )

# ... all other event helpers
```

**Usage in services:**
```python
# Example: In Cartographe

from courier_client import CourierClient, events

class CartographeService:
    def __init__(self):
        self.courier = CourierClient(
            url="http://courier:8766",
            service_name="cartographe"
        )
    
    async def run_backtest(
        self,
        backtest_id: str,
        user_id: str,
        tsdl: str,
        parameters: dict
    ):
        # Publish started event
        channel, event_type, data = events.backtest_started(
            backtest_id=backtest_id,
            job_id=f"job_{backtest_id}",
            user_id=user_id,
            parameters=parameters
        )
        await self.courier.publish(channel, event_type, data)
        
        # Run backtest with progress updates
        for progress in [0.25, 0.5, 0.75]:
            # ... backtest logic ...
            
            channel, event_type, data = events.backtest_progress(
                backtest_id=backtest_id,
                job_id=f"job_{backtest_id}",
                user_id=user_id,
                progress=progress,
                stage="calculating",
                message=f"Processing... {int(progress * 100)}%"
            )
            await self.courier.publish(channel, event_type, data)
        
        # Publish completed
        # ...
```

---

#### Task 3.2: TypeScript Client Library (2 days)

**Objective:** Easy integration for frontend

**Create package:**
```
lumiere-frontend/
└── lib/
    └── courier/
        ├── client.ts
        ├── events.ts
        ├── router.ts
        └── hooks.ts
```

**Implementation:**

```typescript
// lib/courier/client.ts

export class CourierClient {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 3000;
  
  constructor(
    private url: string,
    private channel: string,
    private token: string
  ) {}
  
  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      const wsUrl = `${this.url}/ws/${this.channel}?token=${this.token}`;
      this.ws = new WebSocket(wsUrl);
      
      this.ws.onopen = () => {
        console.log(`Connected to Courier: ${this.channel}`);
        this.reconnectAttempts = 0;
        resolve();
      };
      
      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        reject(error);
      };
      
      this.ws.onclose = (event) => {
        console.log('WebSocket closed:', event.code, event.reason);
        this.handleReconnect();
      };
    });
  }
  
  private handleReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnect attempts reached');
      return;
    }
    
    this.reconnectAttempts++;
    const delay = this.reconnectDelay * this.reconnectAttempts;
    
    console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);
    
    setTimeout(() => {
      this.connect().catch(console.error);
    }, delay);
  }
  
  onMessage(handler: (event: CourierEvent) => void) {
    if (!this.ws) throw new Error('Not connected');
    
    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        // Handle ping/pong
        if (data === 'ping') {
          this.ws?.send('pong');
          return;
        }
        
        handler(data);
      } catch (error) {
        console.error('Failed to parse message:', error);
      }
    };
  }
  
  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}
```

**Event router:**
```typescript
// lib/courier/router.ts

import type { CourierEvent } from './events';

type EventHandler<T extends CourierEvent = CourierEvent> = (
  event: T
) => void | Promise<void>;

export class EventRouter {
  private handlers = new Map<string, EventHandler>();
  
  on<T extends CourierEvent>(
    eventType: T['type'],
    handler: EventHandler<T>
  ): void {
    this.handlers.set(eventType, handler as EventHandler);
  }
  
  off(eventType: string): void {
    this.handlers.delete(eventType);
  }
  
  async route(event: CourierEvent): Promise<void> {
    const handler = this.handlers.get(event.type);
    
    if (handler) {
      try {
        await handler(event);
      } catch (error) {
        console.error(`Error handling event ${event.type}:`, error);
      }
    }
  }
}
```

**React hook:**
```typescript
// lib/courier/hooks.ts

import { useEffect, useRef, useState } from 'react';
import { CourierClient } from './client';
import { EventRouter } from './router';
import type { CourierEvent } from './events';

export function useCourier(userId: string) {
  const clientRef = useRef<CourierClient | null>(null);
  const routerRef = useRef(new EventRouter());
  const [isConnected, setIsConnected] = useState(false);
  
  useEffect(() => {
    const token = localStorage.getItem('auth_token');
    if (!token) return;
    
    const client = new CourierClient(
      process.env.NEXT_PUBLIC_COURIER_URL!,
      `user.${userId}`,
      token
    );
    
    client.connect()
      .then(() => {
        setIsConnected(true);
        
        client.onMessage((event: CourierEvent) => {
          routerRef.current.route(event);
        });
      })
      .catch(console.error);
    
    clientRef.current = client;
    
    return () => {
      client.disconnect();
    };
  }, [userId]);
  
  return {
    isConnected,
    router: routerRef.current
  };
}
```

**Usage in components:**
```typescript
// Example: BacktestDashboard component

import { useCourier } from '@/lib/courier/hooks';
import { useAuth } from '@/hooks/useAuth';

export function BacktestDashboard() {
  const { user } = useAuth();
  const { router, isConnected } = useCourier(user.id);
  const [progress, setProgress] = useState(0);
  
  useEffect(() => {
    router.on('backtest.started', (event) => {
      console.log('Backtest started:', event.backtest_id);
    });
    
    router.on('backtest.progress', (event) => {
      setProgress(event.progress);
    });
    
    router.on('backtest.completed', (event) => {
      setProgress(1);
      showResults(event.summary);
    });
    
    return () => {
      router.off('backtest.started');
      router.off('backtest.progress');
      router.off('backtest.completed');
    };
  }, [router]);
  
  return (
    <div>
      <ConnectionStatus isConnected={isConnected} />
      <ProgressBar value={progress * 100} />
    </div>
  );
}
```

---

#### Task 3.3: Service Integration (3 days)

**Integrate each service:**

**Prophet:**
- [ ] Publish `prophet.message_chunk` during streaming
- [ ] Publish `prophet.tsdl_ready` when TSDL generated
- [ ] Publish `prophet.error` on errors

**Cartographe:**
- [ ] Publish `backtest.started` when backtest begins
- [ ] Publish `backtest.progress` at 25%, 50%, 75%
- [ ] Publish `backtest.completed` with results
- [ ] Publish `backtest.failed` on errors

**Chevalier:**
- [ ] Publish `strategy.deployed` on deployment
- [ ] Publish `trade.signal_generated` for signals
- [ ] Publish `trade.order_filled` on fills
- [ ] Publish `position.closed` on closes

**Frontend:**
- [ ] Connect to Courier on user login
- [ ] Handle all event types
- [ ] Display real-time updates
- [ ] Reconnect on disconnect

---

## 5. Phase 4: Scaling & Advanced Features

**Duration:** 1 week  
**Goal:** Prepare for scale and add nice-to-have features  
**Priority:** MEDIUM - Can wait until after launch

### 5.1 Task Breakdown

#### Task 4.1: Redis Pub/Sub for Multi-Instance (3 days)

**Objective:** Scale Courier horizontally

**Current limitation:** In-process pub/sub only works with single instance

**Solution:** Use Redis pub/sub for cross-instance communication

```python
# courier/src/courier/infrastructure/redis_broker.py

import redis.asyncio as redis
import json
from typing import Dict, Set

class RedisEventBroker:
    """
    Redis-based event broker for multi-instance deployment
    
    Architecture:
    - Each Courier instance manages local WebSocket connections
    - Events published to Redis pub/sub
    - All instances receive events and forward to local clients
    """
    
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)
        self.pubsub = self.redis.pubsub()
        self.subscribed_channels: Set[str] = set()
    
    async def subscribe_to_channel(self, channel: str):
        """Subscribe to Redis channel"""
        if channel not in self.subscribed_channels:
            await self.pubsub.subscribe(channel)
            self.subscribed_channels.add(channel)
    
    async def publish_event(
        self,
        channel: str,
        event: Dict
    ):
        """Publish event to Redis"""
        await self.redis.publish(
            channel,
            json.dumps(event)
        )
    
    async def listen(self):
        """Listen for events from Redis"""
        async for message in self.pubsub.listen():
            if message['type'] == 'message':
                channel = message['channel'].decode()
                event = json.loads(message['data'])
                
                # Forward to local WebSocket clients
                await self.forward_to_local_clients(channel, event)
    
    async def forward_to_local_clients(
        self,
        channel: str,
        event: Dict
    ):
        """Forward event to local WebSocket connections"""
        # Implementation delegates to local broker
        pass
```

---

#### Task 4.2: Event Persistence & Replay (2 days)

**Objective:** Allow clients to replay missed events

```python
# courier/src/courier/infrastructure/event_store.py

import redis.asyncio as redis
from datetime import datetime, timedelta
from typing import List, Dict
import json

class EventStore:
    """
    Store recent events for replay on reconnect
    
    Uses Redis sorted sets with timestamp scores
    TTL: 1 hour (configurable)
    """
    
    def __init__(
        self,
        redis_client: redis.Redis,
        ttl_seconds: int = 3600
    ):
        self.redis = redis_client
        self.ttl = ttl_seconds
    
    async def store_event(
        self,
        channel: str,
        event: Dict
    ):
        """Store event with timestamp"""
        key = f"events:{channel}"
        score = datetime.utcnow().timestamp()
        value = json.dumps(event)
        
        # Add to sorted set
        await self.redis.zadd(key, {value: score})
        
        # Set expiration
        await self.redis.expire(key, self.ttl)
    
    async def get_events_since(
        self,
        channel: str,
        since: datetime
    ) -> List[Dict]:
        """Get events since timestamp"""
        key = f"events:{channel}"
        min_score = since.timestamp()
        max_score = datetime.utcnow().timestamp()
        
        # Get events in range
        events = await self.redis.zrangebyscore(
            key,
            min_score,
            max_score
        )
        
        return [json.loads(e) for e in events]
```

**WebSocket replay on connect:**
```python
@router.websocket("/ws/{channel}")
async def websocket_endpoint(
    websocket: WebSocket,
    channel: str,
    token: str = Query(...),
    since: str = Query(None)  # ISO timestamp
):
    # ... authentication ...
    
    await websocket.accept()
    
    # Replay missed events
    if since:
        since_dt = datetime.fromisoformat(since.replace('Z', '+00:00'))
        missed_events = await event_store.get_events_since(
            channel,
            since_dt
        )
        
        for event in missed_events:
            await websocket.send_json(event)
    
    # Continue with live events
    # ...
```

---

#### Task 4.3: Admin Dashboard (2 days)

**Objective:** Web UI for monitoring Courier

```python
# courier/src/courier/api/admin.py

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse

router = APIRouter()

@router.get("/admin", response_class=HTMLResponse)
async def admin_dashboard():
    """Admin dashboard HTML"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Courier Admin</title>
        <style>
            body { font-family: monospace; margin: 20px; }
            .metric { margin: 10px 0; }
            .channel { background: #f0f0f0; padding: 10px; margin: 5px 0; }
        </style>
    </head>
    <body>
        <h1>Courier Event Bus - Admin Dashboard</h1>
        
        <div id="stats"></div>
        <div id="channels"></div>
        
        <script>
            async function fetchStats() {
                const response = await fetch('/stats');
                const data = await response.json();
                
                document.getElementById('stats').innerHTML = `
                    <h2>Statistics</h2>
                    <div class="metric">Active Connections: ${data.total_connections}</div>
                    <div class="metric">Active Channels: ${data.active_channels}</div>
                    <div class="metric">Messages Sent: ${data.total_messages_sent}</div>
                    <div class="metric">Uptime: ${data.uptime_seconds}s</div>
                `;
                
                let channelsHtml = '<h2>Active Channels</h2>';
                for (const [channel, count] of Object.entries(data.channels || {})) {
                    channelsHtml += `
                        <div class="channel">
                            <strong>${channel}</strong>: ${count} connections
                        </div>
                    `;
                }
                document.getElementById('channels').innerHTML = channelsHtml;
            }
            
            // Refresh every 5 seconds
            setInterval(fetchStats, 5000);
            fetchStats();
        </script>
    </body>
    </html>
    """

@router.get("/admin/channels")
async def list_channels():
    """List all active channels with connection counts"""
    return {
        "channels": broker.get_channel_stats()
    }

@router.get("/admin/connections")
async def list_connections():
    """List all active connections"""
    return {
        "connections": broker.get_connection_details()
    }
```

---

## 6. Testing Strategy

### 6.1 Unit Tests

**Coverage target: 80%+**

```python
# courier/tests/unit/test_jwt_verifier.py
# courier/tests/unit/test_rate_limiter.py
# courier/tests/unit/test_event_validation.py
# courier/tests/unit/test_event_router.py
```

### 6.2 Integration Tests

```python
# courier/tests/integration/test_websocket_auth.py
# courier/tests/integration/test_publish_endpoint.py
# courier/tests/integration/test_event_delivery.py
# courier/tests/integration/test_reconnection.py
```

### 6.3 E2E Tests

```python
# courier/tests/e2e/test_complete_backtest_flow.py

async def test_complete_backtest_flow():
    """
    Test complete flow:
    1. Frontend connects to WebSocket
    2. Cartographe publishes backtest events
    3. Frontend receives events in correct order
    """
    
    # Connect frontend client
    client = CourierClient(...)
    await client.connect()
    
    received_events = []
    client.onMessage(lambda e: received_events.append(e))
    
    # Publish events from backend
    await cartographe_client.publish_backtest_started(...)
    await asyncio.sleep(0.1)
    
    await cartographe_client.publish_backtest_progress(...)
    await asyncio.sleep(0.1)
    
    await cartographe_client.publish_backtest_completed(...)
    await asyncio.sleep(0.1)
    
    # Verify events received
    assert len(received_events) == 3
    assert received_events[0]['type'] == 'backtest.started'
    assert received_events[1]['type'] == 'backtest.progress'
    assert received_events[2]['type'] == 'backtest.completed'
```

### 6.4 Load Tests

```python
# courier/tests/load/test_concurrent_connections.py

import asyncio
from locust import HttpUser, task, between

class CourierUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def publish_event(self):
        self.client.post(
            "/publish",
            json={
                "channel": f"user.{self.user_id}",
                "data": {
                    "type": "test.event",
                    "source": "load-test",
                    "test_data": "..."
                }
            },
            headers={"X-Service-Name": "load-test"}
        )

# Run: locust -f test_concurrent_connections.py --users 1000 --spawn-rate 10
```

**Load test targets:**
- 1000+ concurrent WebSocket connections
- 10,000+ events/second throughput
- <50ms p99 latency

---

## 7. Deployment Plan

### 7.1 Development Environment

```bash
# Deploy to development
cd ~/lumiere/lumiere-public/courier

# Build Docker image
docker build -f Dockerfile --target development -t courier:dev .

# Run with docker-compose
docker-compose up -d courier

# Verify
curl http://localhost:8766/health
```

### 7.2 Production Environment

```bash
# Build production image
docker build -f Dockerfile --target production -t courier:1.0.0 .

# Tag for registry
docker tag courier:1.0.0 localhost:5000/courier:1.0.0

# Push to registry (if using)
docker push localhost:5000/courier:1.0.0

# Update systemd service
sudo systemctl restart courier

# Verify
sudo systemctl status courier
sudo journalctl -u courier -f
```

### 7.3 Deployment Checklist

**Pre-deployment:**
- [ ] All tests passing
- [ ] Code review complete
- [ ] Documentation updated
- [ ] Changelog created
- [ ] Backup current version
- [ ] Database migrations (if any)

**Deployment:**
- [ ] Deploy to development first
- [ ] Smoke tests in development
- [ ] Deploy to staging (if exists)
- [ ] Production deployment during maintenance window
- [ ] Monitor logs for 1 hour
- [ ] Verify metrics in Grafana

**Post-deployment:**
- [ ] Health check passing
- [ ] WebSocket connections working
- [ ] Events being published/received
- [ ] No error spikes in logs
- [ ] Performance metrics normal

---

## 8. Rollback Procedures

### 8.1 Immediate Rollback

If critical issues detected within 1 hour:

```bash
# Stop current version
sudo systemctl stop courier

# Revert to previous Docker image
docker tag courier:previous courier:latest

# Start service
sudo systemctl start courier

# Verify
curl http://localhost:8766/health
```

### 8.2 Data Rollback

If Redis data corrupted:

```bash
# Flush Redis (if using persistence)
redis-cli FLUSHDB

# Restart Courier
sudo systemctl restart courier
```

### 8.3 Rollback Decision Tree

```
Issue Detected
    ↓
Critical? (Service Down / Data Loss / Security Breach)
    ↓ YES
Immediate Rollback
    ↓ NO
High Impact? (>50% Users Affected)
    ↓ YES
Schedule Rollback (within 1 hour)
    ↓ NO
Monitor & Fix Forward
```

---

## 9. Timeline Summary

```
Week 1: Phase 1 - MVP Security & Validation
├── Day 1-2: WebSocket Authentication
├── Day 3-4: Event Schema Validation
├── Day 5:   Rate Limiting
└── Day 6-7: Graceful Shutdown + Testing

Week 2: Phase 2 - Production Hardening
├── Day 1-2: Prometheus Metrics
├── Day 3:   Health Check Enhancement
├── Day 4:   Structured Logging
└── Day 5-7: Error Tracking + Testing

Week 3: Phase 3 - Service Integration
├── Day 1-2: Python Client Library
├── Day 3-4: TypeScript Client Library
└── Day 5-7: Service Integration (Prophet, Cartographe, Chevalier, Frontend)

Week 4: Phase 4 - Scaling & Advanced (Optional)
├── Day 1-3: Redis Pub/Sub Multi-Instance
├── Day 4-5: Event Persistence & Replay
└── Day 6-7: Admin Dashboard + Final Testing
```

---

## 10. Success Criteria

### Phase 1 (MVP)
- [x] WebSocket connections require authentication
- [x] Invalid events are rejected
- [x] Rate limiting prevents abuse
- [x] Graceful shutdown works
- [x] All tests passing

### Phase 2 (Production)
- [x] Metrics exported to Prometheus
- [x] Grafana dashboard operational
- [x] Structured logging in place
- [x] Health checks comprehensive

### Phase 3 (Integration)
- [x] Python client library published
- [x] TypeScript client library in frontend
- [x] Prophet publishes events
- [x] Cartographe publishes events
- [x] Chevalier publishes events
- [x] Frontend receives and displays events

### Phase 4 (Scale)
- [x] Redis pub/sub working
- [x] Event replay functional
- [x] Admin dashboard accessible
- [x] Load tests passing

---

## 11. Risk Mitigation

### Risk 1: Breaking Changes to Existing Services

**Mitigation:**
- Backwards-compatible API (keep old endpoints during transition)
- Feature flags for new functionality
- Gradual rollout (Prophet first, then Cartographe, etc.)

### Risk 2: Performance Degradation

**Mitigation:**
- Load testing before production
- Monitoring metrics closely
- Rollback plan ready
- Rate limiting to prevent overload

### Risk 3: Data Loss

**Mitigation:**
- Events are ephemeral (no persistence in MVP)
- Event replay optional (Phase 4)
- Services should handle missed events gracefully

### Risk 4: Security Vulnerabilities

**Mitigation:**
- JWT authentication mandatory
- Authorization checks enforced
- Regular security audits
- Rate limiting prevents DoS

---

**END OF IMPLEMENTATION PLAN**

**Version:** 1.0  
**Last Updated:** October 26, 2025  
**Status:** Ready for Implementation  
**Estimated Completion:** 4 weeks from start1~# Courier Implementation Plan
## Complete Roadmap from Current State to Production-Ready Event Bus

**Version:** 1.0  
**Date:** October 26, 2025  
**Target Completion:** 4 weeks  
**Status:** Planning Phase

---

## Table of Contents

1. [Current State Analysis](#1-current-state-analysis)
2. [Phase 1: MVP Security & Validation](#2-phase-1-mvp-security--validation)
3. [Phase 2: Production Hardening](#3-phase-2-production-hardening)
4. [Phase 3: Service Integration](#4-phase-3-service-integration)
5. [Phase 4: Scaling & Advanced Features](#5-phase-4-scaling--advanced-features)
6. [Testing Strategy](#6-testing-strategy)
7. [Deployment Plan](#7-deployment-plan)
8. [Rollback Procedures](#8-rollback-procedures)

---

## 1. Current State Analysis

### 1.1 What Exists (According to HLD v1.2)

**Core Features:**
- ✅ FastAPI WebSocket server
- ✅ Channel-based routing (`global`, `user.*`, `strategy.*`, `forge.job.*`)
- ✅ Dynamic channel creation
- ✅ HTTP publish endpoints (POST /publish, POST /publish/{channel})
- ✅ WebSocket endpoint (WS /ws/{channel})
- ✅ Connection management (heartbeat, cleanup)
- ✅ Health check (GET /health)
- ✅ Statistics (GET /stats)

**Architecture:**
- ✅ In-process pub/sub (no external dependencies)
- ✅ Stateless broker (no persistence)
- ✅ systemd service deployment

### 1.2 Critical Gaps

**Security:**
- ❌ No WebSocket authentication
- ❌ No authorization checks
- ❌ No rate limiting

**Data Quality:**
- ❌ No event schema validation
- ❌ No payload size limits
- ❌ No malformed data protection

**Production Readiness:**
- ❌ No graceful shutdown
- ❌ No metrics/monitoring
- ❌ No event persistence
- ❌ No replay capability

**Integration:**
- ❌ Services not publishing events
- ❌ Frontend not consuming events
- ❌ No client libraries

---

## 2. Phase 1: MVP Security & Validation

**Duration:** 1 week  
**Goal:** Make Courier secure and validate data integrity  
**Priority:** CRITICAL - Cannot deploy without this

### 2.1 Task Breakdown

#### Task 1.1: WebSocket Authentication (2 days)

**Objective:** Verify JWT tokens and authorize channel access

**Files to Create/Modify:**
```
courier/
├── src/courier/
│   ├── domain/
│   │   └── auth.py                    # NEW: Auth domain models
│   ├── infrastructure/
│   │   └── jwt_verifier.py            # NEW: JWT verification
│   └── api/
│       └── websocket.py               # MODIFY: Add auth
```

**Implementation:**

**Step 1:** Create auth domain models
```python
# courier/src/courier/domain/auth.py

from pydantic import BaseModel
from typing import Optional

class TokenPayload(BaseModel):
    user_id: str
    wallet_address: str
    exp: int
    iat: int

class AuthenticatedClient(BaseModel):
    user_id: str
    wallet_address: str
    channel: str
    connected_at: str
```

**Step 2:** Create JWT verifier
```python
# courier/src/courier/infrastructure/jwt_verifier.py

import jwt
from datetime import datetime
from courier.domain.auth import TokenPayload
from courier.config.settings import settings

class JWTVerifier:
    def __init__(self, secret: str, algorithm: str = "HS256"):
        self.secret = secret
        self.algorithm = algorithm
    
    def verify_token(self, token: str) -> TokenPayload:
        """Verify JWT token and return payload"""
        try:
            payload = jwt.decode(
                token,
                self.secret,
                algorithms=[self.algorithm]
            )
            return TokenPayload(**payload)
        except jwt.ExpiredSignatureError:
            raise ValueError("Token expired")
        except jwt.InvalidTokenError:
            raise ValueError("Invalid token")
    
    def verify_channel_access(
        self, 
        user_id: str, 
        channel: str
    ) -> bool:
        """Verify user can access channel"""
        
        # Global channel - everyone can read
        if channel == "global":
            return True
        
        # User channel - must match user_id
        if channel.startswith("user."):
            channel_user_id = channel.split(".")[1]
            return channel_user_id == user_id
        
        # Strategy channel - check ownership in database
        if channel.startswith("strategy."):
            # TODO: Query Architect to verify strategy ownership
            return True
        
        # Backtest channel - ephemeral, assume authorized
        if channel.startswith("backtest."):
            return True
        
        # Forge job channel - ephemeral, assume authorized
        if channel.startswith("forge.job."):
            return True
        
        return False
```

**Step 3:** Modify WebSocket endpoint
```python
# courier/src/courier/api/websocket.py

from fastapi import WebSocket, WebSocketDisconnect, Query, status
from typing import Optional
from courier.infrastructure.jwt_verifier import JWTVerifier
from courier.config.settings import settings

jwt_verifier = JWTVerifier(secret=settings.JWT_SECRET)

@router.websocket("/ws/{channel}")
async def websocket_endpoint(
    websocket: WebSocket,
    channel: str,
    token: Optional[str] = Query(None)
):
    """WebSocket endpoint with authentication"""
    
    # Verify token presence
    if not token:
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Authentication token required"
        )
        return
    
    # Verify token validity
    try:
        token_payload = jwt_verifier.verify_token(token)
    except ValueError as e:
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION,
            reason=str(e)
        )
        return
    
    # Verify channel access
    if not jwt_verifier.verify_channel_access(token_payload.user_id, channel):
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Unauthorized access to channel"
        )
        return
    
    # Accept connection
    await websocket.accept()
    
    reporter.info(
        "WebSocket client connected",
        context="WebSocket",
        channel=channel,
        user_id=token_payload.user_id,
        verbose_level=2
    )
    
    # Register client with user_id
    await broker.subscribe(
        channel, 
        websocket,
        user_id=token_payload.user_id
    )
    
    try:
        # Heartbeat loop
        while True:
            try:
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0
                )
                # Handle ping/pong
                if data == "ping":
                    await websocket.send_text("pong")
            except asyncio.TimeoutError:
                # Send ping
                await websocket.send_text("ping")
    
    except WebSocketDisconnect:
        reporter.info(
            "WebSocket client disconnected",
            context="WebSocket",
            channel=channel,
            user_id=token_payload.user_id,
            verbose_level=2
        )
        await broker.unsubscribe(channel, websocket)
```

**Step 4:** Update settings
```python
# courier/src/courier/config/settings.py

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Existing settings...
    
    # JWT Authentication
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    
    class Config:
        env_file = ".env"

settings = Settings()
```

**Step 5:** Update environment files
```bash
# courier/config/production.yaml
jwt:
  secret: ${JWT_SECRET}  # From environment
  algorithm: "HS256"

# courier/config/development.yaml
jwt:
  secret: "dev-secret-change-in-production"
  algorithm: "HS256"
```

**Acceptance Criteria:**
- [ ] WebSocket connection requires valid JWT token
- [ ] Token expiration is enforced
- [ ] User can only access authorized channels
- [ ] Unauthorized access returns 1008 policy violation
- [ ] User ID is logged with all connections

---

#### Task 1.2: Event Schema Validation (2 days)

**Objective:** Validate all published events against schema

**Files to Create/Modify:**
```
courier/
├── src/courier/
│   ├── domain/
│   │   ├── events/
│   │   │   ├── __init__.py
│   │   │   ├── base.py               # NEW: Base event
│   │   │   ├── prophet.py            # NEW: Prophet events
│   │   │   ├── backtest.py           # NEW: Backtest events
│   │   │   ├── trading.py            # NEW: Trading events
│   │   │   └── system.py             # NEW: System events
│   └── api/
│       └── publish.py                # MODIFY: Add validation
```

**Implementation:**

**Step 1:** Create base event
```python
# courier/src/courier/domain/events/base.py

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class BaseEvent(BaseModel):
    """Base event that all events must inherit from"""
    
    type: str = Field(..., description="Event type")
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat() + "Z",
        description="ISO 8601 timestamp"
    )
    source: str = Field(..., description="Publishing service")
    trace_id: Optional[str] = Field(None, description="Correlation ID")
    
    class Config:
        json_schema_extra = {
            "example": {
                "type": "event.action",
                "timestamp": "2025-10-26T10:00:00.000Z",
                "source": "service_name",
                "trace_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        }
```

**Step 2:** Create Prophet events
```python
# courier/src/courier/domain/events/prophet.py

from typing import Literal, Dict, List
from pydantic import Field
from .base import BaseEvent

class ProphetMessageChunk(BaseEvent):
    type: Literal["prophet.message_chunk"]
    conversation_id: str
    chunk: str
    is_final: bool

class ProphetTSDLReady(BaseEvent):
    type: Literal["prophet.tsdl_ready"]
    conversation_id: str
    tsdl: str
    metadata: Dict[str, any] = Field(
        ...,
        description="Strategy metadata"
    )

class ProphetError(BaseEvent):
    type: Literal["prophet.error"]
    conversation_id: str
    error_code: str
    message: str
    details: str = Field(default="")

# Union type
ProphetEvent = (
    ProphetMessageChunk | 
    ProphetTSDLReady | 
    ProphetError
)
```

**Step 3:** Create Backtest events
```python
# courier/src/courier/domain/events/backtest.py

from typing import Literal, Dict
from pydantic import Field, field_validator
from .base import BaseEvent

class BacktestStarted(BaseEvent):
    type: Literal["backtest.started"]
    backtest_id: str
    job_id: str
    user_id: str
    parameters: Dict[str, any]

class BacktestProgress(BaseEvent):
    type: Literal["backtest.progress"]
    backtest_id: str
    job_id: str
    user_id: str
    progress: float = Field(..., ge=0.0, le=1.0)
    stage: str
    message: str
    
    @field_validator('progress')
    def validate_progress(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Progress must be between 0.0 and 1.0')
        return v

class BacktestCompleted(BaseEvent):
    type: Literal["backtest.completed"]
    backtest_id: str
    job_id: str
    user_id: str
    duration_seconds: int
    summary: Dict[str, any]

class BacktestFailed(BaseEvent):
    type: Literal["backtest.failed"]
    backtest_id: str
    job_id: str
    user_id: str
    error_code: str
    message: str
    details: str = Field(default="")

class BacktestCancelled(BaseEvent):
    type: Literal["backtest.cancelled"]
    backtest_id: str
    job_id: str
    user_id: str
    reason: str
    progress_at_cancellation: float

# Union type
BacktestEvent = (
    BacktestStarted |
    BacktestProgress |
    BacktestCompleted |
    BacktestFailed |
    BacktestCancelled
)
```

**Step 4:** Create Trading events
```python
# courier/src/courier/domain/events/trading.py

from typing import Literal
from pydantic import Field
from .base import BaseEvent

class StrategyDeployed(BaseEvent):
    type: Literal["strategy.deployed"]
    strategy_id: str
    user_id: str
    name: str
    initial_capital: float
    token_pair: str
    status: Literal["active"]

class TradeSignalGenerated(BaseEvent):
    type: Literal["trade.signal_generated"]
    strategy_id: str
    user_id: str
    signal_id: str
    token: str
    direction: Literal["buy", "sell"]
    confidence: float = Field(..., ge=0.0, le=1.0)
    reason: str
    price_at_signal: float

class TradeOrderFilled(BaseEvent):
    type: Literal["trade.order_filled"]
    strategy_id: str
    user_id: str
    order_id: str
    token: str
    direction: Literal["buy", "sell"]
    fill_price: float
    fill_amount: float
    total_value: float
    fees: float
    tx_signature: str

class PositionClosed(BaseEvent):
    type: Literal["position.closed"]
    strategy_id: str
    user_id: str
    position_id: str
    token: str
    entry_price: float
    exit_price: float
    size: float
    realized_pnl: float
    realized_pnl_percentage: float
    reason: Literal["take_profit", "stop_loss", "manual", "signal"]
    tx_signature: str

# Union type
TradingEvent = (
    StrategyDeployed |
    TradeSignalGenerated |
    TradeOrderFilled |
    PositionClosed
    # ... add all 12 trading events
)
```

**Step 5:** Create master event union
```python
# courier/src/courier/domain/events/__init__.py

from typing import Union
from .prophet import ProphetEvent
from .backtest import BacktestEvent
from .trading import TradingEvent
from .system import SystemEvent

# Master union type for all events
CourierEvent = Union[
    ProphetEvent,
    BacktestEvent,
    TradingEvent,
    SystemEvent
]

# Export all event types
__all__ = [
    "CourierEvent",
    "ProphetEvent",
    "BacktestEvent",
    "TradingEvent",
    "SystemEvent"
]
```

**Step 6:** Update publish endpoint
```python
# courier/src/courier/api/publish.py

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel, ValidationError
from typing import Dict, Any
from courier.domain.events import CourierEvent

router = APIRouter()

class PublishRequest(BaseModel):
    channel: str
    data: Dict[str, Any]

@router.post("/publish")
async def publish_event(
    request: PublishRequest,
    x_service_name: str = Header(..., alias="X-Service-Name")
):
    """
    Publish event to channel with schema validation
    
    Headers:
        X-Service-Name: Name of publishing service
    """
    
    # Validate event schema
    try:
        # Pydantic will validate against CourierEvent union
        validated_event = CourierEvent.model_validate(request.data)
    except ValidationError as e:
        reporter.error(
            "Event schema validation failed",
            context="Publish",
            channel=request.channel,
            service=x_service_name,
            errors=e.errors(),
            verbose_level=1
        )
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Invalid event schema",
                "validation_errors": e.errors()
            }
        )
    
    # Verify source matches header
    if validated_event.source != x_service_name:
        raise HTTPException(
            status_code=400,
            detail="Event source must match X-Service-Name header"
        )
    
    # Publish to broker
    clients_reached = await broker.publish(
        request.channel,
        validated_event.model_dump()
    )
    
    reporter.info(
        "Event published",
        context="Publish",
        channel=request.channel,
        event_type=validated_event.type,
        clients_reached=clients_reached,
        verbose_level=2
    )
    
    return {
        "status": "published",
        "channel": request.channel,
        "event_type": validated_event.type,
        "clients_reached": clients_reached,
        "timestamp": validated_event.timestamp
    }
```

**Acceptance Criteria:**
- [ ] All event types have Pydantic models
- [ ] Invalid events are rejected with 400
- [ ] Validation errors are descriptive
- [ ] Event source matches service header
- [ ] All fields are validated (types, ranges, enums)

---

#### Task 1.3: Rate Limiting (1 day)

**Objective:** Prevent abuse of publish endpoint

**Files to Create:**
```
courier/
├── src/courier/
│   ├── infrastructure/
│   │   └── rate_limiter.py           # NEW
│   └── api/
│       └── publish.py                # MODIFY
```

**Implementation:**

```python
# courier/src/courier/infrastructure/rate_limiter.py

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List

class RateLimiter:
    """
    Simple in-memory rate limiter using sliding window
    
    For production with multiple instances, use Redis
    """
    
    def __init__(
        self,
        limit: int = 100,
        window_seconds: int = 60
    ):
        self.limit = limit
        self.window = timedelta(seconds=window_seconds)
        self.requests: Dict[str, List[datetime]] = defaultdict(list)
    
    async def check_rate_limit(self, identifier: str) -> bool:
        """
        Check if identifier is within rate limit
        
        Returns:
            True if allowed, False if rate limit exceeded
        """
        now = datetime.utcnow()
        cutoff = now - self.window
        
        # Remove expired timestamps
        self.requests[identifier] = [
            ts for ts in self.requests[identifier]
            if ts > cutoff
        ]
        
        # Check limit
        if len(self.requests[identifier]) >= self.limit:
            return False
        
        # Add current request
        self.requests[identifier].append(now)
        return True
    
    def get_remaining(self, identifier: str) -> int:
        """Get remaining requests in current window"""
        return max(0, self.limit - len(self.requests[identifier]))
    
    def get_reset_time(self, identifier: str) -> datetime:
        """Get time when rate limit resets"""
        if not self.requests[identifier]:
            return datetime.utcnow()
        
        oldest = min(self.requests[identifier])
        return oldest + self.window
```

**Usage in publish endpoint:**
```python
# courier/src/courier/api/publish.py

from courier.infrastructure.rate_limiter import RateLimiter

# Initialize rate limiter
# 100 requests per minute per service
rate_limiter = RateLimiter(limit=100, window_seconds=60)

@router.post("/publish")
async def publish_event(
    request: PublishRequest,
    x_service_name: str = Header(..., alias="X-Service-Name")
):
    """Publish event with rate limiting"""
    
    # Check rate limit
    if not await rate_limiter.check_rate_limit(x_service_name):
        remaining = rate_limiter.get_remaining(x_service_name)
        reset_time = rate_limiter.get_reset_time(x_service_name)
        
        reporter.warning(
            "Rate limit exceeded",
            context="Publish",
            service=x_service_name,
            remaining=remaining,
            verbose_level=1
        )
        
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Rate limit exceeded",
                "limit": rate_limiter.limit,
                "window_seconds": rate_limiter.window.total_seconds(),
                "remaining": remaining,
                "reset_at": reset_time.isoformat() + "Z"
            }
        )
    
    # ... rest of publish logic ...
```

**Acceptance Criteria:**
- [ ] Services limited to 100 requests/minute
- [ ] Rate limit per service (not global)
- [ ] 429 response with reset time
- [ ] Headers show remaining requests

---

#### Task 1.4: Graceful Shutdown (1 day)

**Objective:** Close connections cleanly on shutdown

**Files to Modify:**
```
courier/
└── src/courier/
    └── main.py                        # MODIFY
```

**Implementation:**

```python
# courier/src/courier/main.py

import signal
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager
    Handles startup and shutdown logic
    """
    
    # Startup
    reporter.info(
        "Courier starting up",
        context="Lifecycle",
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
        verbose_level=1
    )
    
    # Setup shutdown event
    shutdown_event = asyncio.Event()
    
    def handle_shutdown(signum, frame):
        """Handle shutdown signals"""
        reporter.info(
            "Shutdown signal received",
            context="Lifecycle",
            signal=signal.Signals(signum).name,
            verbose_level=1
        )
        shutdown_event.set()
    
    # Register signal handlers
    signal.signal(signal.SIGTERM, handle_shutdown)
    signal.signal(signal.SIGINT, handle_shutdown)
    
    yield
    
    # Shutdown
    reporter.info(
        "Courier shutting down",
        context="Lifecycle",
        verbose_level=1
    )
    
    # Close all WebSocket connections gracefully
    await broker.close_all_connections(
        reason="Server shutting down for maintenance"
    )
    
    reporter.info(
        "All connections closed",
        context="Lifecycle",
        verbose_level=1
    )
    
    # Wait a moment for final cleanup
    await asyncio.sleep(1)
    
    reporter.info(
        "Courier shutdown complete",
        context="Lifecycle",
        verbose_level=1
    )

# Create app with lifespan
app = FastAPI(
    title="Courier Event Bus",
    version=settings.VERSION,
    lifespan=lifespan
)
```

**Update broker to support graceful shutdown:**
```python
# courier/src/courier/core/broker.py

class EventBroker:
    async def close_all_connections(self, reason: str = "Server shutdown"):
        """Close all WebSocket connections gracefully"""
        
        reporter.info(
            "Closing all WebSocket connections",
            context="Broker",
            total_connections=len(self.get_all_clients()),
            verbose_level=1
        )
        
        close_tasks = []
        
        for channel, clients in self.clients.items():
            for websocket in clients:
                close_tasks.append(
                    websocket.close(
                        code=status.WS_1001_GOING_AWAY,
                        reason=reason
                    )
                )
        
        # Close all connections concurrently
        await asyncio.gather(*close_tasks, return_exceptions=True)
        
        # Clear client registry
        self.clients.clear()
        self.client_metadata.clear()
        
        reporter.info(
            "All connections closed",
            context="Broker",
            verbose_level=1
        )
```

**Acceptance Criteria:**
- [ ] SIGTERM triggers graceful shutdown
- [ ] SIGINT (Ctrl+C) triggers graceful shutdown
- [ ] All WebSocket connections close with 1001 code
- [ ] Shutdown reason sent to clients
- [ ] No errors during shutdown

---

### 2.2 Phase 1 Testing

**Create integration tests:**
```python
# courier/tests/integration/test_auth.py

import pytest
from fastapi.testclient import TestClient
import jwt

def test_websocket_requires_token(client: TestClient):
    """WebSocket connection must provide token"""
    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect("/ws/user.123"):
            pass
    assert exc.value.code == 1008

def test_websocket_rejects_invalid_token(client: TestClient):
    """Invalid token is rejected"""
    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect("/ws/user.123?token=invalid"):
            pass
    assert exc.value.code == 1008

def test_websocket_rejects_unauthorized_channel(client: TestClient):
    """User cannot access other user's channel"""
    token = create_test_token(user_id="user_123")
    
    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect(f"/ws/user.456?token={token}"):
            pass
    assert exc.value.code == 1008

def test_websocket_accepts_valid_token(client: TestClient):
    """Valid token allows connection"""
    token = create_test_token(user_id="user_123")
    
    with client.websocket_connect(f"/ws/user.123?token={token}") as ws:
        ws.send_text("ping")
        data = ws.receive_text()
        assert data == "pong"
```

```python
# courier/tests/integration/test_validation.py

def test_publish_validates_event_schema(client: TestClient):
    """Invalid event schema is rejected"""
    response = client.post(
        "/publish",
        json={
            "channel": "user.123",
            "data": {
                "type": "invalid.event",
                "invalid_field": "value"
            }
        },
        headers={"X-Service-Name": "test"}
    )
    assert response.status_code == 400
    assert "validation_errors" in response.json()["detail"]

def test_publish_accepts_valid_event(client: TestClient):
    """Valid event is accepted"""
    response = client.post(
        "/publish",
        json={
            "channel": "user.123",
            "data": {
                "type": "backtest.started",
                "source": "test",
                "backtest_id": "bt_123",
                "job_id": "job_xyz",
                "user_id": "user_123",
                "parameters": {
                    "timeframe": {"start": "2024-01-01", "end": "2024-12-31"},
                    "initial_capital": 10000,
                    "token_pair": "SOL/USDC"
                }
            }
        },
        headers={"X-Service-Name": "test"}
    )
    assert response.status_code == 200
```

```python
# courier/tests/integration/test_rate_limiting.py

def test_rate_limit_enforced(client: TestClient):
    """Rate limit is enforced"""
    
    # Make 100 requests (limit)
    for i in range(100):
        response = client.post(
            "/publish",
            json=create_valid_event(),
            headers={"X-Service-Name": "test"}
        )
        assert response.status_code == 200
    
    # 101st request should be rate limited
    response = client.post(
        "/publish",
        json=create_valid_event(),
        headers={"X-Service-Name": "test"}
    )
    assert response.status_code == 429
    assert "rate limit exceeded" in response.json()["detail"]["error"].lower()
```

### 2.3 Phase 1 Deployment

**Steps:**
1. Create feature branch: `git checkout -b feature/phase-1-security`
2. Implement all tasks
3. Run full test suite: `pytest -v`
4. Update documentation
5. Code review
6. Merge to develop
7. Deploy to development environment
8. Smoke tests
9. Deploy to production

**Rollback Plan:**
- Keep old version running during deployment
- If issues detected, revert systemd service to old version
- Monitor logs for 1 hour after deployment

---

## 3. Phase 2: Production Hardening

**Duration:** 1 week  
**Goal:** Add monitoring, metrics, and operational tools  
**Priority:** HIGH - Needed for production confidence

### 3.1 Task Breakdown

#### Task 2.1: Prometheus Metrics (2 days)

**Objective:** Export metrics for monitoring

**Files to Create:**
```
courier/
├── src/courier/
│   ├── infrastructure/
│   │   └── metrics.py                # NEW
│   └── api/
│       └── metrics.py                # NEW: Metrics endpoint
```

**Implementation:**

```python
# courier/src/courier/infrastructure/metrics.py

from prometheus_client import (
    Counter, 
    Histogram, 
    Gauge, 
    generate_latest,
    CONTENT_TYPE_LATEST
)

# Event metrics
events_published_total = Counter(
    'courier_events_published_total',
    'Total number of events published',
    ['channel', 'event_type', 'source']
)

events_delivered_total = Counter(
    'courier_events_delivered_total',
    'Total number of events delivered to clients',
    ['channel', 'event_type']
)

events_validation_failed_total = Counter(
    'courier_events_validation_failed_total',
    'Total number of events that failed validation',
    ['event_type', 'source']
)

# Connection metrics
websocket_connections_active = Gauge(
    'courier_websocket_connections_active',
    'Current number of active WebSocket connections',
    ['channel']
)

websocket_connections_total = Counter(
    'courier_websocket_connections_total',
    'Total number of WebSocket connections',
    ['channel']
)

websocket_disconnections_total = Counter(
    'courier_websocket_disconnections_total',
    'Total number of WebSocket disconnections',
    ['channel', 'reason']
)

# Performance metrics
publish_latency_seconds = Histogram(
    'courier_publish_latency_seconds',
    'Time taken to publish event',
    ['channel'],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0)
)

websocket_message_latency_seconds = Histogram(
    'courier_websocket_message_latency_seconds',
    'Time taken to deliver message to WebSocket client',
    ['channel'],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0)
)

# Rate limiting metrics
rate_limit_exceeded_total = Counter(
    'courier_rate_limit_exceeded_total',
    'Total number of rate limit violations',
    ['service']
)

# Error metrics
errors_total = Counter(
    'courier_errors_total',
    'Total number of errors',
    ['error_type', 'component']
)
```

**Metrics endpoint:**
```python
# courier/src/courier/api/metrics.py

from fastapi import APIRouter, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from courier.infrastructure.metrics import *

router = APIRouter()

@router.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )
```

**Instrument publish endpoint:**
```python
# courier/src/courier/api/publish.py

from courier.infrastructure.metrics import (
    events_published_total,
    events_validation_failed_total,
    publish_latency_seconds,
    rate_limit_exceeded_total
)

@router.post("/publish")
async def publish_event(request: PublishRequest, ...):
    # Rate limiting
    if not await rate_limiter.check_rate_limit(x_service_name):
        rate_limit_exceeded_total.labels(service=x_service_name).inc()
        raise HTTPException(...)
    
    # Validation
    try:
        validated_event = CourierEvent.model_validate(request.data)
    except ValidationError as e:
        events_validation_failed_total.labels(
            event_type=request.data.get('type', 'unknown'),
            source=x_service_name
        ).inc()
        raise HTTPException(...)
    
    # Publish with timing
    with publish_latency_seconds.labels(channel=request.channel).time():
        clients_reached = await broker.publish(
            request.channel,
            validated_event.model_dump()
        )
    
    # Record metrics
    events_published_total.labels(
        channel=request.channel,
        event_type=validated_event.type,
        source=validated_event.source
    ).inc()
    
    return {...}
```

**Acceptance Criteria:**
- [ ] Metrics exported at /metrics
- [ ] All key operations instrumented
- [ ] Prometheus can scrape metrics
- [ ] Grafana dashboard created

---

#### Task 2.2: Health Check Enhancement (1 day)

**Objective:** More detailed health information

```python
# courier/src/courier/api/health.py

from fastapi import APIRouter
from datetime import datetime
from courier.core.broker import broker

router = APIRouter()

@router.get("/health")
async def health_check():
    """Enhanced health check with component status"""
    
    start_time = broker.start_time or datetime.utcnow()
    uptime_seconds = (datetime.utcnow() - start_time).total_seconds()
    
    # Check components
    components = {
        "broker": "healthy",
        "rate_limiter": "healthy",
        "jwt_verifier": "healthy"
    }
    
    # Overall status
    status = "healthy" if all(
        c == "healthy" for c in components.values()
    ) else "degraded"
    
    return {
        "status": status,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "uptime_seconds": int(uptime_seconds),
        "components": components,
        "metrics": {
            "active_connections": broker.get_connection_count(),
            "active_channels": len(broker.clients),
            "total_messages_sent": broker.total_messages_sent,
            "total_messages_received": broker.total_messages_received
        },
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

@router.get("/health/live")
async def liveness_check():
    """Kubernetes liveness probe"""
    return {"status": "alive"}

@router.get("/health/ready")
async def readiness_check():
    """Kubernetes readiness probe"""
    # Check if service is ready to accept connections
    is_ready = broker.is_initialized()
    
    return {
        "status": "ready" if is_ready else "not_ready",
        "ready": is_ready
    }
```

---

#### Task 2.3: Structured Logging Enhancement (1 day)

**Objective:** Consistent, searchable logs

```python
# courier/src/courier/infrastructure/logging.py

import json
from datetime import datetime
from typing import Dict, Any

class StructuredLogger:
    """
    Structured JSON logging for production
    Compatible with ELK, Loki, CloudWatch
    """
    
    def __init__(self, service_name: str):
        self.service_name = service_name
    
    def _log(
        self, 
        level: str, 
        message: str,
        **kwargs
    ):
        """Emit structured log entry"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": level,
            "service": self.service_name,
            "message": message,
            **kwargs
        }
        
        print(json.dumps(log_entry))
    
    def info(self, message: str, **kwargs):
        self._log("INFO", message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        self._log("WARNING", message, **kwargs)
    
    def error(self, message: str, **kwargs):
        self._log("ERROR", message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        self._log("DEBUG", message, **kwargs)

# Usage
logger = StructuredLogger("courier")

logger.info(
    "Event published",
    channel="user.123",
    event_type="backtest.started",
    clients_reached=2
)
# Output: {"timestamp": "...", "level": "INFO", "service": "courier", 
#          "message": "Event published", "channel": "user.123", ...}
```

---

#### Task 2.4: Error Tracking Integration (1 day)

**Objective:** Capture and track errors (Sentry optional)

```python
# courier/src/courier/infrastructure/error_tracking.py

import sys
import traceback
from typing import Optional, Dict, Any

class ErrorTracker:
    """
    Error tracking and aggregation
    Can integrate with Sentry in production
    """
    
    def __init__(self):
        self.errors: Dict[str, int] = {}
    
    def capture_exception(
        self,
        exception: Exception,
        context: Optional[Dict[str, Any]] = None
    ):
        """Capture exception with context"""
        
        error_type = type(exception).__name__
        error_message = str(exception)
        stack_trace = ''.join(
            traceback.format_exception(*sys.exc_info())
        )
        
        # Count errors
        self.errors[error_type] = self.errors.get(error_type, 0) + 1
        
        # Log structured error
        logger.error(
            f"Exception occurred: {error_message}",
            error_type=error_type,
            error_count=self.errors[error_type],
            stack_trace=stack_trace,
            context=context or {}
        )
        
        # TODO: Send to Sentry if configured
        # if settings.SENTRY_DSN:
        #     sentry_sdk.capture_exception(exception)
    
    def get_error_stats(self) -> Dict[str, int]:
        """Get error statistics"""
        return self.errors.copy()

error_tracker = ErrorTracker()
```

---

### 3.2 Phase 2 Deliverables

**Monitoring:**
- [ ] Prometheus metrics exported
- [ ] Grafana dashboard created
- [ ] Alerts configured (high error rate, low uptime)

**Observability:**
- [ ] Structured JSON logging
- [ ] Error tracking system
- [ ] Enhanced health checks

**Documentation:**
- [ ] Metrics documentation
- [ ] Grafana dashboard screenshots
- [ ] Runbook for common issues

---

## 4. Phase 3: Service Integration

**Duration:** 1 week  
**Goal:** Integrate backend services and frontend  
**Priority:** HIGH - Core functionality

### 4.1 Task Breakdown

#### Task 3.1: Python Client Library (2 days)

**Objective:** Easy integration for backend services

**Create new package:**
```
lumiere-public/
└── courier-client-python/
    ├── pyproject.toml
    ├── src/
    │   └── courier_client/
    │       ├── __init__.py
    │       ├── client.py
    │       └── events.py
    └── tests/
        └── test_client.py
```

**Implementation:**

```python
# courier-client-python/src/courier_client/client.py

import httpx
from datetime import datetime
from typing import Dict, Any, Optional

class CourierClient:
    """
    Python client for publishing events to Courier
    
    Usage:
        courier = CourierClient(
            url="http://courier:8766",
            service_name="prophet"
        )
        
        await courier.publish(
            channel="user.123",
            event_type="prophet.tsdl_ready",
            data={
                "conversation_id": "conv_abc",
                "tsdl": "...",
                "metadata": {...}
            }
        )
    """
    
    def __init__(
        self,
        url: str,
        service_name: str,
        timeout: float = 5.0
    ):
        self.url = url.rstrip('/')
        self.service_name = service_name
        self.client = httpx.AsyncClient(timeout=timeout)
    
    async def publish(
        self,
        channel: str,
        event_type: str,
        data: Dict[str, Any],
        trace_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Publish event to Courier
        
        Args:
            channel: Target channel (e.g., "user.123")
            event_type: Event type (e.g., "backtest.started")
            data: Event-specific data
            trace_id: Optional correlation ID
        
        Returns:
            Response from Courier
        
        Raises:
            httpx.HTTPStatusError: If publish fails
        """
        
        payload = {
            "channel": channel,
            "data": {
                "type": event_type,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "source": self.service_name,
                **({"trace_id": trace_id} if trace_id else {}),
                **data
            }
        }
        
        response = await self.client.post(
            f"{self.url}/publish",
            json=payload,
            headers={"X-Service-Name": self.service_name}
        )
        
        response.raise_for_status()
        return response.json()
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
```

**Helper functions:**
```python
# courier-client-python/src/courier_client/events.py

from typing import Dict, Any

def backtest_started(
    backtest_id: str,
    job_id: str,
    user_id: str,
    parameters: Dict[str, Any]
) -> tuple[str, str, Dict[str, Any]]:
    """
    Helper to create backtest.started event
    
    Returns: (channel, event_type, data)
    """
    return (
        f"user.{user_id}",
        "backtest.started",
        {
            "backtest_id": backtest_id,
            "job_id": job_id,
            "user_id": user_id,
            "parameters": parameters
        }
    )

def backtest_progress(
    backtest_id: str,
    job_id: str,
    user_id: str,
    progress: float,
    stage: str,
    message: str
) -> tuple[str, str, Dict[str, Any]]:
    """Helper to create backtest.progress event"""
    return (
        f"user.{user_id}",
        "backtest.progress",
        {
            "backtest_id": backtest_id,
            "job_id": job_id,
            "user_id": user_id,
            "progress": progress,
            "stage": stage,
            "message": message
        }
    )

# ... all other event helpers
```

**Usage in services:**
```python
# Example: In Cartographe

from courier_client import CourierClient, events

class CartographeService:
    def __init__(self):
        self.courier = CourierClient(
            url="http://courier:8766",
            service_name="cartographe"
        )
    
    async def run_backtest(
        self,
        backtest_id: str,
        user_id: str,
        tsdl: str,
        parameters: dict
    ):
        # Publish started event
        channel, event_type, data = events.backtest_started(
            backtest_id=backtest_id,
            job_id=f"job_{backtest_id}",
            user_id=user_id,
            parameters=parameters
        )
        await self.courier.publish(channel, event_type, data)
        
        # Run backtest with progress updates
        for progress in [0.25, 0.5, 0.75]:
            # ... backtest logic ...
            
            channel, event_type, data = events.backtest_progress(
                backtest_id=backtest_id,
                job_id=f"job_{backtest_id}",
                user_id=user_id,
                progress=progress,
                stage="calculating",
                message=f"Processing... {int(progress * 100)}%"
            )
            await self.courier.publish(channel, event_type, data)
        
        # Publish completed
        # ...
```

---

#### Task 3.2: TypeScript Client Library (2 days)

**Objective:** Easy integration for frontend

**Create package:**
```
lumiere-frontend/
└── lib/
    └── courier/
        ├── client.ts
        ├── events.ts
        ├── router.ts
        └── hooks.ts
```

**Implementation:**

```typescript
// lib/courier/client.ts

export class CourierClient {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 3000;
  
  constructor(
    private url: string,
    private channel: string,
    private token: string
  ) {}
  
  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      const wsUrl = `${this.url}/ws/${this.channel}?token=${this.token}`;
      this.ws = new WebSocket(wsUrl);
      
      this.ws.onopen = () => {
        console.log(`Connected to Courier: ${this.channel}`);
        this.reconnectAttempts = 0;
        resolve();
      };
      
      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        reject(error);
      };
      
      this.ws.onclose = (event) => {
        console.log('WebSocket closed:', event.code, event.reason);
        this.handleReconnect();
      };
    });
  }
  
  private handleReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnect attempts reached');
      return;
    }
    
    this.reconnectAttempts++;
    const delay = this.reconnectDelay * this.reconnectAttempts;
    
    console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);
    
    setTimeout(() => {
      this.connect().catch(console.error);
    }, delay);
  }
  
  onMessage(handler: (event: CourierEvent) => void) {
    if (!this.ws) throw new Error('Not connected');
    
    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        // Handle ping/pong
        if (data === 'ping') {
          this.ws?.send('pong');
          return;
        }
        
        handler(data);
      } catch (error) {
        console.error('Failed to parse message:', error);
      }
    };
  }
  
  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}
```

**Event router:**
```typescript
// lib/courier/router.ts

import type { CourierEvent } from './events';

type EventHandler<T extends CourierEvent = CourierEvent> = (
  event: T
) => void | Promise<void>;

export class EventRouter {
  private handlers = new Map<string, EventHandler>();
  
  on<T extends CourierEvent>(
    eventType: T['type'],
    handler: EventHandler<T>
  ): void {
    this.handlers.set(eventType, handler as EventHandler);
  }
  
  off(eventType: string): void {
    this.handlers.delete(eventType);
  }
  
  async route(event: CourierEvent): Promise<void> {
    const handler = this.handlers.get(event.type);
    
    if (handler) {
      try {
        await handler(event);
      } catch (error) {
        console.error(`Error handling event ${event.type}:`, error);
      }
    }
  }
}
```

**React hook:**
```typescript
// lib/courier/hooks.ts

import { useEffect, useRef, useState } from 'react';
import { CourierClient } from './client';
import { EventRouter } from './router';
import type { CourierEvent } from './events';

export function useCourier(userId: string) {
  const clientRef = useRef<CourierClient | null>(null);
  const routerRef = useRef(new EventRouter());
  const [isConnected, setIsConnected] = useState(false);
  
  useEffect(() => {
    const token = localStorage.getItem('auth_token');
    if (!token) return;
    
    const client = new CourierClient(
      process.env.NEXT_PUBLIC_COURIER_URL!,
      `user.${userId}`,
      token
    );
    
    client.connect()
      .then(() => {
        setIsConnected(true);
        
        client.onMessage((event: CourierEvent) => {
          routerRef.current.route(event);
        });
      })
      .catch(console.error);
    
    clientRef.current = client;
    
    return () => {
      client.disconnect();
    };
  }, [userId]);
  
  return {
    isConnected,
    router: routerRef.current
  };
}
```

**Usage in components:**
```typescript
// Example: BacktestDashboard component

import { useCourier } from '@/lib/courier/hooks';
import { useAuth } from '@/hooks/useAuth';

export function BacktestDashboard() {
  const { user } = useAuth();
  const { router, isConnected } = useCourier(user.id);
  const [progress, setProgress] = useState(0);
  
  useEffect(() => {
    router.on('backtest.started', (event) => {
      console.log('Backtest started:', event.backtest_id);
    });
    
    router.on('backtest.progress', (event) => {
      setProgress(event.progress);
    });
    
    router.on('backtest.completed', (event) => {
      setProgress(1);
      showResults(event.summary);
    });
    
    return () => {
      router.off('backtest.started');
      router.off('backtest.progress');
      router.off('backtest.completed');
    };
  }, [router]);
  
  return (
    <div>
      <ConnectionStatus isConnected={isConnected} />
      <ProgressBar value={progress * 100} />
    </div>
  );
}
```

---

#### Task 3.3: Service Integration (3 days)

**Integrate each service:**

**Prophet:**
- [ ] Publish `prophet.message_chunk` during streaming
- [ ] Publish `prophet.tsdl_ready` when TSDL generated
- [ ] Publish `prophet.error` on errors

**Cartographe:**
- [ ] Publish `backtest.started` when backtest begins
- [ ] Publish `backtest.progress` at 25%, 50%, 75%
- [ ] Publish `backtest.completed` with results
- [ ] Publish `backtest.failed` on errors

**Chevalier:**
- [ ] Publish `strategy.deployed` on deployment
- [ ] Publish `trade.signal_generated` for signals
- [ ] Publish `trade.order_filled` on fills
- [ ] Publish `position.closed` on closes

**Frontend:**
- [ ] Connect to Courier on user login
- [ ] Handle all event types
- [ ] Display real-time updates
- [ ] Reconnect on disconnect

---

## 5. Phase 4: Scaling & Advanced Features

**Duration:** 1 week  
**Goal:** Prepare for scale and add nice-to-have features  
**Priority:** MEDIUM - Can wait until after launch

### 5.1 Task Breakdown

#### Task 4.1: Redis Pub/Sub for Multi-Instance (3 days)

**Objective:** Scale Courier horizontally

**Current limitation:** In-process pub/sub only works with single instance

**Solution:** Use Redis pub/sub for cross-instance communication

```python
# courier/src/courier/infrastructure/redis_broker.py

import redis.asyncio as redis
import json
from typing import Dict, Set

class RedisEventBroker:
    """
    Redis-based event broker for multi-instance deployment
    
    Architecture:
    - Each Courier instance manages local WebSocket connections
    - Events published to Redis pub/sub
    - All instances receive events and forward to local clients
    """
    
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)
        self.pubsub = self.redis.pubsub()
        self.subscribed_channels: Set[str] = set()
    
    async def subscribe_to_channel(self, channel: str):
        """Subscribe to Redis channel"""
        if channel not in self.subscribed_channels:
            await self.pubsub.subscribe(channel)
            self.subscribed_channels.add(channel)
    
    async def publish_event(
        self,
        channel: str,
        event: Dict
    ):
        """Publish event to Redis"""
        await self.redis.publish(
            channel,
            json.dumps(event)
        )
    
    async def listen(self):
        """Listen for events from Redis"""
        async for message in self.pubsub.listen():
            if message['type'] == 'message':
                channel = message['channel'].decode()
                event = json.loads(message['data'])
                
                # Forward to local WebSocket clients
                await self.forward_to_local_clients(channel, event)
    
    async def forward_to_local_clients(
        self,
        channel: str,
        event: Dict
    ):
        """Forward event to local WebSocket connections"""
        # Implementation delegates to local broker
        pass
```

---

#### Task 4.2: Event Persistence & Replay (2 days)

**Objective:** Allow clients to replay missed events

```python
# courier/src/courier/infrastructure/event_store.py

import redis.asyncio as redis
from datetime import datetime, timedelta
from typing import List, Dict
import json

class EventStore:
    """
    Store recent events for replay on reconnect
    
    Uses Redis sorted sets with timestamp scores
    TTL: 1 hour (configurable)
    """
    
    def __init__(
        self,
        redis_client: redis.Redis,
        ttl_seconds: int = 3600
    ):
        self.redis = redis_client
        self.ttl = ttl_seconds
    
    async def store_event(
        self,
        channel: str,
        event: Dict
    ):
        """Store event with timestamp"""
        key = f"events:{channel}"
        score = datetime.utcnow().timestamp()
        value = json.dumps(event)
        
        # Add to sorted set
        await self.redis.zadd(key, {value: score})
        
        # Set expiration
        await self.redis.expire(key, self.ttl)
    
    async def get_events_since(
        self,
        channel: str,
        since: datetime
    ) -> List[Dict]:
        """Get events since timestamp"""
        key = f"events:{channel}"
        min_score = since.timestamp()
        max_score = datetime.utcnow().timestamp()
        
        # Get events in range
        events = await self.redis.zrangebyscore(
            key,
            min_score,
            max_score
        )
        
        return [json.loads(e) for e in events]
```

**WebSocket replay on connect:**
```python
@router.websocket("/ws/{channel}")
async def websocket_endpoint(
    websocket: WebSocket,
    channel: str,
    token: str = Query(...),
    since: str = Query(None)  # ISO timestamp
):
    # ... authentication ...
    
    await websocket.accept()
    
    # Replay missed events
    if since:
        since_dt = datetime.fromisoformat(since.replace('Z', '+00:00'))
        missed_events = await event_store.get_events_since(
            channel,
            since_dt
        )
        
        for event in missed_events:
            await websocket.send_json(event)
    
    # Continue with live events
    # ...
```

---

#### Task 4.3: Admin Dashboard (2 days)

**Objective:** Web UI for monitoring Courier

```python
# courier/src/courier/api/admin.py

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse

router = APIRouter()

@router.get("/admin", response_class=HTMLResponse)
async def admin_dashboard():
    """Admin dashboard HTML"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Courier Admin</title>
        <style>
            body { font-family: monospace; margin: 20px; }
            .metric { margin: 10px 0; }
            .channel { background: #f0f0f0; padding: 10px; margin: 5px 0; }
        </style>
    </head>
    <body>
        <h1>Courier Event Bus - Admin Dashboard</h1>
        
        <div id="stats"></div>
        <div id="channels"></div>
        
        <script>
            async function fetchStats() {
                const response = await fetch('/stats');
                const data = await response.json();
                
                document.getElementById('stats').innerHTML = `
                    <h2>Statistics</h2>
                    <div class="metric">Active Connections: ${data.total_connections}</div>
                    <div class="metric">Active Channels: ${data.active_channels}</div>
                    <div class="metric">Messages Sent: ${data.total_messages_sent}</div>
                    <div class="metric">Uptime: ${data.uptime_seconds}s</div>
                `;
                
                let channelsHtml = '<h2>Active Channels</h2>';
                for (const [channel, count] of Object.entries(data.channels || {})) {
                    channelsHtml += `
                        <div class="channel">
                            <strong>${channel}</strong>: ${count} connections
                        </div>
                    `;
                }
                document.getElementById('channels').innerHTML = channelsHtml;
            }
            
            // Refresh every 5 seconds
            setInterval(fetchStats, 5000);
            fetchStats();
        </script>
    </body>
    </html>
    """

@router.get("/admin/channels")
async def list_channels():
    """List all active channels with connection counts"""
    return {
        "channels": broker.get_channel_stats()
    }

@router.get("/admin/connections")
async def list_connections():
    """List all active connections"""
    return {
        "connections": broker.get_connection_details()
    }
```

---

## 6. Testing Strategy

### 6.1 Unit Tests

**Coverage target: 80%+**

```python
# courier/tests/unit/test_jwt_verifier.py
# courier/tests/unit/test_rate_limiter.py
# courier/tests/unit/test_event_validation.py
# courier/tests/unit/test_event_router.py
```

### 6.2 Integration Tests

```python
# courier/tests/integration/test_websocket_auth.py
# courier/tests/integration/test_publish_endpoint.py
# courier/tests/integration/test_event_delivery.py
# courier/tests/integration/test_reconnection.py
```

### 6.3 E2E Tests

```python
# courier/tests/e2e/test_complete_backtest_flow.py

async def test_complete_backtest_flow():
    """
    Test complete flow:
    1. Frontend connects to WebSocket
    2. Cartographe publishes backtest events
    3. Frontend receives events in correct order
    """
    
    # Connect frontend client
    client = CourierClient(...)
    await client.connect()
    
    received_events = []
    client.onMessage(lambda e: received_events.append(e))
    
    # Publish events from backend
    await cartographe_client.publish_backtest_started(...)
    await asyncio.sleep(0.1)
    
    await cartographe_client.publish_backtest_progress(...)
    await asyncio.sleep(0.1)
    
    await cartographe_client.publish_backtest_completed(...)
    await asyncio.sleep(0.1)
    
    # Verify events received
    assert len(received_events) == 3
    assert received_events[0]['type'] == 'backtest.started'
    assert received_events[1]['type'] == 'backtest.progress'
    assert received_events[2]['type'] == 'backtest.completed'
```

### 6.4 Load Tests

```python
# courier/tests/load/test_concurrent_connections.py

import asyncio
from locust import HttpUser, task, between

class CourierUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def publish_event(self):
        self.client.post(
            "/publish",
            json={
                "channel": f"user.{self.user_id}",
                "data": {
                    "type": "test.event",
                    "source": "load-test",
                    "test_data": "..."
                }
            },
            headers={"X-Service-Name": "load-test"}
        )

# Run: locust -f test_concurrent_connections.py --users 1000 --spawn-rate 10
```

**Load test targets:**
- 1000+ concurrent WebSocket connections
- 10,000+ events/second throughput
- <50ms p99 latency

---

## 7. Deployment Plan

### 7.1 Development Environment

```bash
# Deploy to development
cd ~/lumiere/lumiere-public/courier

# Build Docker image
docker build -f Dockerfile --target development -t courier:dev .

# Run with docker-compose
docker-compose up -d courier

# Verify
curl http://localhost:8766/health
```

### 7.2 Production Environment

```bash
# Build production image
docker build -f Dockerfile --target production -t courier:1.0.0 .

# Tag for registry
docker tag courier:1.0.0 localhost:5000/courier:1.0.0

# Push to registry (if using)
docker push localhost:5000/courier:1.0.0

# Update systemd service
sudo systemctl restart courier

# Verify
sudo systemctl status courier
sudo journalctl -u courier -f
```

### 7.3 Deployment Checklist

**Pre-deployment:**
- [ ] All tests passing
- [ ] Code review complete
- [ ] Documentation updated
- [ ] Changelog created
- [ ] Backup current version
- [ ] Database migrations (if any)

**Deployment:**
- [ ] Deploy to development first
- [ ] Smoke tests in development
- [ ] Deploy to staging (if exists)
- [ ] Production deployment during maintenance window
- [ ] Monitor logs for 1 hour
- [ ] Verify metrics in Grafana

**Post-deployment:**
- [ ] Health check passing
- [ ] WebSocket connections working
- [ ] Events being published/received
- [ ] No error spikes in logs
- [ ] Performance metrics normal

---

## 8. Rollback Procedures

### 8.1 Immediate Rollback

If critical issues detected within 1 hour:

```bash
# Stop current version
sudo systemctl stop courier

# Revert to previous Docker image
docker tag courier:previous courier:latest

# Start service
sudo systemctl start courier

# Verify
curl http://localhost:8766/health
```

### 8.2 Data Rollback

If Redis data corrupted:

```bash
# Flush Redis (if using persistence)
redis-cli FLUSHDB

# Restart Courier
sudo systemctl restart courier
```

### 8.3 Rollback Decision Tree

```
Issue Detected
    ↓
Critical? (Service Down / Data Loss / Security Breach)
    ↓ YES
Immediate Rollback
    ↓ NO
High Impact? (>50% Users Affected)
    ↓ YES
Schedule Rollback (within 1 hour)
    ↓ NO
Monitor & Fix Forward
```

---

## 9. Timeline Summary

```
Week 1: Phase 1 - MVP Security & Validation
├── Day 1-2: WebSocket Authentication
├── Day 3-4: Event Schema Validation
├── Day 5:   Rate Limiting
└── Day 6-7: Graceful Shutdown + Testing

Week 2: Phase 2 - Production Hardening
├── Day 1-2: Prometheus Metrics
├── Day 3:   Health Check Enhancement
├── Day 4:   Structured Logging
└── Day 5-7: Error Tracking + Testing

Week 3: Phase 3 - Service Integration
├── Day 1-2: Python Client Library
├── Day 3-4: TypeScript Client Library
└── Day 5-7: Service Integration (Prophet, Cartographe, Chevalier, Frontend)

Week 4: Phase 4 - Scaling & Advanced (Optional)
├── Day 1-3: Redis Pub/Sub Multi-Instance
├── Day 4-5: Event Persistence & Replay
└── Day 6-7: Admin Dashboard + Final Testing
```

---

## 10. Success Criteria

### Phase 1 (MVP)
- [x] WebSocket connections require authentication
- [x] Invalid events are rejected
- [x] Rate limiting prevents abuse
- [x] Graceful shutdown works
- [x] All tests passing

### Phase 2 (Production)
- [x] Metrics exported to Prometheus
- [x] Grafana dashboard operational
- [x] Structured logging in place
- [x] Health checks comprehensive

### Phase 3 (Integration)
- [x] Python client library published
- [x] TypeScript client library in frontend
- [x] Prophet publishes events
- [x] Cartographe publishes events
- [x] Chevalier publishes events
- [x] Frontend receives and displays events

### Phase 4 (Scale)
- [x] Redis pub/sub working
- [x] Event replay functional
- [x] Admin dashboard accessible
- [x] Load tests passing

---

## 11. Risk Mitigation

### Risk 1: Breaking Changes to Existing Services

**Mitigation:**
- Backwards-compatible API (keep old endpoints during transition)
- Feature flags for new functionality
- Gradual rollout (Prophet first, then Cartographe, etc.)

### Risk 2: Performance Degradation

**Mitigation:**
- Load testing before production
- Monitoring metrics closely
- Rollback plan ready
- Rate limiting to prevent overload

### Risk 3: Data Loss

**Mitigation:**
- Events are ephemeral (no persistence in MVP)
- Event replay optional (Phase 4)
- Services should handle missed events gracefully

### Risk 4: Security Vulnerabilities

**Mitigation:**
- JWT authentication mandatory
- Authorization checks enforced
- Regular security audits
- Rate limiting prevents DoS

---

**END OF IMPLEMENTATION PLAN**

**Version:** 1.0  
**Last Updated:** October 26, 2025  
**Status:** Ready for Implementation  
**Estimated Completion:** 4 weeks from start

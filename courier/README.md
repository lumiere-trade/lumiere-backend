# Courier - Event Bus Service

**WebSocket-based event broadcasting hub for real-time communication across Lumiere services.**

---

## Overview

Courier is a lightweight pub/sub event broker that enables real-time communication between Lumiere backend services and frontend clients. It provides WebSocket connections for clients and HTTP endpoints for backend services to publish events.

**Name Origin:** *Courier* = "messenger" or "one who delivers messages"

**Architecture:** Channel-based message routing with dynamic channel creation

---

## Features

### Event Broadcasting
- Pub/sub messaging pattern
- Channel-based event routing
- Multi-client support per channel
- Dynamic channel creation

### WebSocket Server
- Real-time bidirectional communication
- Connection lifecycle management
- Automatic heartbeat/ping-pong
- Dead connection cleanup

### HTTP Publishing
- Dual publish endpoints (URL and body-based)
- Auto-channel creation for dynamic workflows
- Event validation and error handling

---

## Architecture
```
┌─────────────────┐
│  Backend Service│
│   (Pourtier)    │
└────────┬────────┘
         │ HTTP POST /publish
         ▼
┌─────────────────┐
│ Courier Broker  │
│  (WebSocket)    │
└────────┬────────┘
         │ broadcast
         ├──────────► Client 1 (channel: user.123)
         ├──────────► Client 2 (channel: global)
         └──────────► Client 3 (channel: forge.job.abc)
```

### Event Flow

1. **Backend service** publishes event via HTTP POST
2. **Courier** validates and routes to channel subscribers
3. **WebSocket clients** receive event in real-time
4. Clients process event and update UI

---

## Quick Start

### Prerequisites
```bash
# System requirements
Python 3.11+
```

### Installation
```bash
# Install dependencies
pip install -e .
```

### Configuration

Create `courier/config/courier.yaml`:
```yaml
# Server Configuration
host: "127.0.0.1"
port: 8766
log_level: "info"

# Channels
channels:
  - "global"
  - "alerts"
  - "user.updates"
  - "strategy.events"

# Connection Settings
max_clients_per_channel: 100
heartbeat_interval: 30  # seconds

# Logging
log_dir: "logs/broker"
verbose: 1
```

### Run Broker
```bash
# Start Courier
python -m courier.broker

# Or specify port
python -m courier.broker 8766

# Server available at ws://localhost:8766
```

---

## Publishing Events (Backend)

### Method 1: Channel in URL (Legacy)
```python
import httpx

async def publish_event():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8766/publish/user.123",
            json={
                "type": "subscription.created",
                "data": {
                    "plan": "pro",
                    "expires_at": "2025-12-31"
                }
            }
        )
        print(response.json())
```

### Method 2: Channel in Body (Recommended)
```python
import httpx

async def publish_event():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8766/publish",
            json={
                "channel": "user.123",
                "data": {
                    "type": "subscription.created",
                    "data": {
                        "plan": "pro",
                        "expires_at": "2025-12-31"
                    }
                }
            }
        )
        print(response.json())

# Response:
# {
#   "status": "published",
#   "channel": "user.123",
#   "clients_reached": 2,
#   "timestamp": "2025-10-16T12:34:56.789Z"
# }
```

### Dynamic Channel Creation

Channels are auto-created on first use:
```python
# Publish to non-existent channel (auto-creates it)
await client.post(
    "http://localhost:8766/publish",
    json={
        "channel": "forge.job.abc-123",  # New dynamic channel
        "data": {
            "type": "progress",
            "progress": 50,
            "message": "Processing data..."
        }
    }
)
```

---

## Subscribing to Events (Frontend)

### JavaScript/TypeScript
```javascript
// Connect to Courier
const ws = new WebSocket('ws://localhost:8766/ws/user.123');

ws.onopen = () => {
  console.log('Connected to channel: user.123');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  // Handle ping (heartbeat)
  if (data.type === 'ping') {
    return;
  }
  
  // Handle actual events
  console.log('Event received:', data);
  
  switch(data.type) {
    case 'subscription.created':
      updateSubscriptionUI(data.data);
      break;
    case 'escrow.deposit':
      updateBalanceUI(data.data);
      break;
  }
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('Disconnected from Courier');
  // Implement reconnection logic
  setTimeout(() => reconnect(), 5000);
};
```

### Python Client
```python
from shared.courier_client import CourierClient

# Connect to channel
client = CourierClient(url="ws://localhost:8766/ws/user.123")
await client.connect()

# Listen for events
async for event in client.listen():
    if event.get('type') == 'ping':
        continue  # Skip heartbeat
    
    print(f"Event: {event}")
    
    # Handle events
    if event['type'] == 'subscription.expired':
        await handle_subscription_expired(event['data'])
```

---

## Channels

### Channel Naming Convention
```
global                  # System-wide broadcasts
alerts                  # Platform alerts
user.<user_id>          # User-specific events
strategy.<strategy_id>  # Strategy updates
forge.job.<job_id>      # Dynamic FORGE job channels
```

### Channel Features

- **Pre-configured channels:** Defined in `courier.yaml`
- **Dynamic channels:** Auto-created on first publish/subscribe
- **Per-channel limits:** Configurable max clients per channel
- **Auto-cleanup:** Unused channels persist until server restart

---

## API Endpoints

### WebSocket
```bash
GET /ws/{channel}  # Connect to channel
```

### HTTP (Publishing)
```bash
POST /publish/{channel}  # Publish to channel (legacy)
POST /publish            # Publish with channel in body (recommended)
```

### Monitoring
```bash
GET /health              # Health check + active clients
GET /stats               # Detailed statistics
```

---

## Monitoring

### Health Check
```bash
curl http://localhost:8766/health

# Response:
{
  "status": "healthy",
  "uptime_seconds": 3600,
  "total_clients": 42,
  "channels": {
    "global": 10,
    "user.123": 2,
    "forge.job.abc": 1
  }
}
```

### Statistics
```bash
curl http://localhost:8766/stats

# Response:
{
  "uptime_seconds": 3600,
  "total_connections": 150,
  "total_messages_sent": 5000,
  "total_messages_received": 250,
  "active_clients": 42,
  "channels": {
    "global": {
      "active_clients": 10,
      "max_clients": 100
    }
  }
}
```

---

## Event Format

### Standard Event Structure
```json
{
  "type": "event.type",
  "data": {
    "key": "value"
  },
  "timestamp": "2025-10-16T12:34:56.789Z"
}
```

### Heartbeat (System)
```json
{
  "type": "ping"
}
```

Clients should ignore `ping` messages (heartbeat monitoring).

---

## Testing
```bash
# Test WebSocket connection
python -c "
import asyncio
import websockets

async def test():
    async with websockets.connect('ws://localhost:8766/ws/test') as ws:
        print('Connected!')
        message = await ws.recv()
        print(f'Received: {message}')

asyncio.run(test())
"

# Test HTTP publish
curl -X POST http://localhost:8766/publish \
  -H "Content-Type: application/json" \
  -d '{
    "channel": "test",
    "data": {
      "type": "test.message",
      "message": "Hello Courier!"
    }
  }'
```

---

## Development

### Code Standards

- **PEP8 compliant**
- **Type hints** for all functions
- **Async/await** pattern
- **Comprehensive error handling**

### Adding Features
```python
# Example: Custom event validation
async def _validate_event(self, event: dict) -> bool:
    required_fields = ['type', 'data']
    return all(field in event for field in required_fields)
```

---

## Performance

### Configuration Tips

- Set `max_clients_per_channel` based on expected load
- Adjust `heartbeat_interval` (default: 30s)
- Use appropriate `log_level` (info for prod, debug for dev)

### Scalability

Current implementation is single-server. For production scale:
- Deploy multiple Courier instances with load balancer
- Use Redis pub/sub for multi-server coordination
- Implement sticky sessions for WebSocket connections
- Monitor connection counts and message throughput

---

## Troubleshooting

### Broker Won't Start
```bash
# Check if port is available
lsof -i :8766

# Check Python version
python --version  # Should be 3.11+

# Check dependencies
pip list | grep fastapi
```

### Client Can't Connect
```bash
# Test WebSocket endpoint
wscat -c ws://localhost:8766/ws/test

# Check broker logs
tail -f logs/broker/broker.log
```

### Events Not Received

- Verify client connected to correct channel
- Check event published to correct channel
- Verify WebSocket connection is active
- Check broker logs for errors

---

## Related Components

- [Pourtier](../pourtier) - Main event publisher
- [Shared](../shared) - CourierClient implementation
- All Lumiere services - Event consumers

---

## License

Apache License 2.0 - See [LICENSE](../LICENSE)

---

**Questions?** Open an issue or contact: dev@lumiere.trade

# Service Discovery with Docker DNS

## Overview

Lumière uses **Docker's built-in DNS** for service discovery. Services communicate using service names instead of hardcoded IPs or ports, enabling seamless container orchestration and scalability.

---

## Architecture
```
┌─────────────────────────────────────────────────┐
│         docker-compose.yaml                     │
│         (Orchestration Layer)                   │
└─────────────────────────────────────────────────┘
                    │
        ┌───────────┼───────────┬───────────┐
        ▼           ▼           ▼           ▼
    ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐
    │Postgres│  │Pourtier│  │Courier │  │Passeur │
    │:5432   │  │:8000   │  │:8765   │  │:8766   │
    └────────┘  └────────┘  └────────┘  └────────┘
         │          │          │          │
         └──────────┴──────────┴──────────┘
              lumiere-network (Docker DNS)
```

**Key Benefits:**
- Automatic DNS resolution: `http://pourtier:8000` resolves to container IP
- Automatic updates when containers restart
- Built-in load balancing for multiple instances
- Zero external dependencies (no Consul, etcd, etc.)

---

## How It Works

### Docker DNS Resolution

When a service makes a request to `http://pourtier:8000`:

1. **Docker DNS** intercepts the hostname `pourtier`
2. Returns the IP address of the `pourtier` container (e.g., `172.18.0.3`)
3. Request is routed to that container
4. If container restarts, DNS automatically updates to new IP

### Network Configuration

All services run in a single Docker network:
```yaml
networks:
  lumiere-net:
    driver: bridge
    name: lumiere-network
```

Services can communicate using:
- Service names: `http://pourtier:8000` (RECOMMENDED)
- Container IPs: `http://172.18.0.3:8000` (NOT recommended - IPs change!)

---

## Configuration Files

### 1. YAML Configs

Each service has environment-specific configuration:

**Development (`development.yaml`)** - Docker development:
```yaml
# pourtier/config/development.yaml
API_HOST: "0.0.0.0"        # Bind to all interfaces (Docker requirement)
API_PORT: 8000             # Internal port
courier_url: "http://courier:8765"  # Docker DNS name
passeur_url: "http://passeur:8766"
```

**Production (`production.yaml`)** - Production deployment:
```yaml
# pourtier/config/production.yaml
API_HOST: "0.0.0.0"
API_PORT: 8000
courier_url: "http://courier:8765"  # Same Docker DNS
passeur_url: "http://passeur:8766"
```

### 2. Settings Classes

Services load URLs from configuration:
```python
# pourtier/src/pourtier/config/settings.py
class Settings(BaseSettings):
    # Service Discovery (Docker DNS)
    courier_url: str = Field(
        default="http://courier:8765",
        description="Courier service URL (Docker DNS)"
    )
    passeur_url: str = Field(
        default="http://passeur:8766",
        description="Passeur bridge URL (Docker DNS)"
    )
```

### 3. docker-compose.yaml

Services are orchestrated with proper dependencies:
```yaml
services:
  postgres:
    # ... postgres config ...
    networks:
      - lumiere-net
  
  pourtier:
    image: pourtier:development
    environment:
      ENV: development
      # Service URLs loaded from development.yaml
    depends_on:
      postgres:
        condition: service_healthy
    networks:
      - lumiere-net
  
  courier:
    image: courier:development
    depends_on:
      pourtier:
        condition: service_healthy
    networks:
      - lumiere-net
```

---

## Port Mapping

### Internal Ports (Docker Network)

Services communicate using these ports **inside** the Docker network:

| Service | Internal Port | DNS Name |
|---------|--------------|----------|
| Postgres | 5432 | `postgres:5432` |
| Pourtier | 8000 | `pourtier:8000` |
| Courier | 8765 | `courier:8765` |
| Passeur | 8766 | `passeur:8766` |

### External Ports (Host Machine)

Services are exposed to the host via port mapping:
```yaml
ports:
  - "${COURIER_PORT:-8765}:8765"  # Host:Container
```

| Service | External Port | Access From Host |
|---------|--------------|------------------|
| Pourtier | 8000 | `http://localhost:8000` |
| Courier | 8765 | `http://localhost:8765` |
| Passeur | 8766 | `http://localhost:8766` |

**Note:** Postgres has NO external port - only accessible internally via Docker DNS.

---

## Usage

### Starting Services
```bash
# Start all services
cd ~/lumiere/lumiere-public
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f pourtier
```

### Stopping Services
```bash
# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: deletes data!)
docker-compose down -v
```

### Restarting a Single Service
```bash
# Restart pourtier
docker-compose restart pourtier

# Rebuild and restart
docker-compose up -d --build pourtier
```

---

## Testing Service Discovery

### DNS Resolution Test

Check if services can resolve each other:
```bash
# From Courier container, resolve Pourtier
docker exec lumiere-courier getent hosts pourtier
# Output: 172.18.0.3      pourtier

# From Pourtier container, resolve Postgres
docker exec lumiere-pourtier getent hosts postgres
# Output: 172.18.0.2      postgres
```

### HTTP Communication Test

Test actual HTTP requests between services:
```bash
# From Courier, make HTTP request to Pourtier
docker exec lumiere-courier curl -s http://pourtier:8000/health

# From Pourtier, check if Postgres is reachable
docker exec lumiere-pourtier pg_isready -h postgres -U postgres
```

### Health Check Test
```bash
# External health checks (from host)
curl http://localhost:8765/health  # Courier
curl http://localhost:8000/health  # Pourtier
curl http://localhost:8766/health  # Passeur

# Internal health checks (Docker DNS)
docker exec lumiere-courier curl -s http://pourtier:8000/health
```

---

## Scaling Services

Docker DNS supports automatic load balancing for multiple instances:

### Manual Scaling
```bash
# Start 3 instances of Pourtier
docker-compose up -d --scale pourtier=3

# Check instances
docker-compose ps pourtier
# Output:
# lumiere-pourtier-1
# lumiere-pourtier-2
# lumiere-pourtier-3

# DNS resolution returns all IPs (round-robin)
docker exec lumiere-courier nslookup pourtier
```

### Load Balancing

Docker automatically balances requests across instances:
```
Request 1 → pourtier-1 (172.18.0.3)
Request 2 → pourtier-2 (172.18.0.4)
Request 3 → pourtier-3 (172.18.0.5)
Request 4 → pourtier-1 (round-robin)
```

**Note:** For scaling beyond 1 instance, remove `container_name` from docker-compose.yaml to avoid conflicts.

---

## Environment Variables

Configuration can be overridden via environment variables:

### .env File
```bash
# .env
ENV=development
COURIER_PORT=8765
POURTIER_PORT=8000

# Override service URLs (optional)
# pourtier_url=http://custom-host:8000
```

### Runtime Override
```bash
# Override at runtime
POURTIER_PORT=9000 docker-compose up -d
```

---

## Troubleshooting

### Issue: "Could not resolve host: pourtier"

**Cause:** Services not in same Docker network

**Solution:**
```bash
# Check networks
docker network inspect lumiere-network

# Verify all services are in the network
docker-compose ps
```

### Issue: "Connection refused"

**Cause:** Service not ready or health check failing

**Solution:**
```bash
# Check service logs
docker-compose logs pourtier

# Check health status
docker-compose ps

# Wait for health check to pass
docker inspect lumiere-pourtier --format='{{.State.Health.Status}}'
```

### Issue: Port conflicts

**Cause:** Port already in use on host

**Solution:**
```bash
# Check what's using the port
sudo lsof -i :8765

# Change external port in .env
echo "COURIER_PORT=8775" >> .env
docker-compose down && docker-compose up -d
```

### Issue: Service can't connect to another service

**Diagnosis:**
```bash
# Test DNS resolution
docker exec lumiere-courier getent hosts pourtier

# Test connectivity
docker exec lumiere-courier ping -c 3 pourtier

# Test HTTP
docker exec lumiere-courier curl -v http://pourtier:8000/health
```

---

## Development Workflow

### Local Development (without Docker)

For local development outside Docker, use `localhost`:
```yaml
# local-override.yaml (not in repo)
courier_url: "http://localhost:8765"
pourtier_url: "http://localhost:8000"
```

### Docker Development (recommended)

Use the standard `development.yaml` configs with Docker DNS.

### Switching Between Environments
```bash
# Development
ENV=development docker-compose up -d

# Production
ENV=production docker-compose -f docker-compose.production.yaml up -d
```

---

## Best Practices

### DO:

- Use service names for communication: `http://pourtier:8000`
- Configure services via YAML and environment variables
- Use health checks and `depends_on` with conditions
- Test DNS resolution when adding new services
- Keep external ports configurable via `.env`

### DON'T:

- Hardcode IPs: `http://172.18.0.3:8000`
- Hardcode `localhost` in Docker configs
- Skip health checks for critical services
- Use static IPs unless absolutely necessary
- Expose unnecessary ports externally

---

## Architecture Decisions

### Why Docker DNS?

**Alternatives considered:**
- **Consul** - Too complex, external dependency
- **etcd** - Overkill for our use case
- **Custom registry** - Reinventing the wheel
- **Environment variables** - Not dynamic, requires restarts

**Why Docker DNS wins:**
- Built-in (zero dependencies)
- Automatic updates
- Production-ready
- Works everywhere (dev, staging, prod)
- Load balancing included
- Simple to understand and maintain

### Configuration Strategy

**3-tier configuration:**

1. **default.yaml** - Base settings for all environments
2. **development.yaml** - Docker development overrides
3. **production.yaml** - Production overrides

**Priority:** ENV vars > environment YAML > default YAML > Pydantic defaults

---

## Migration from Hardcoded URLs

If you have existing code with hardcoded URLs:

### Before:
```python
# Bad: Hardcoded
url = "http://localhost:8000/api/trades"
response = requests.post(url, json=data)
```

### After:
```python
# Good: Config-based
from pourtier.config.settings import get_settings

settings = get_settings()
url = f"{settings.courier_url}/api/trades"
response = requests.post(url, json=data)
```

---

## Monitoring

### Service Health
```bash
# All services status
docker-compose ps

# Individual health check
docker inspect lumiere-pourtier --format='{{.State.Health.Status}}'

# Health endpoint
curl http://localhost:8000/health | jq .
```

### Network Inspection
```bash
# View network details
docker network inspect lumiere-network

# See all containers in network
docker network inspect lumiere-network | jq '.[0].Containers'

# DNS test
docker exec lumiere-courier nslookup pourtier
```

### Logs
```bash
# All logs
docker-compose logs

# Specific service
docker-compose logs -f pourtier

# Last 100 lines
docker-compose logs --tail=100 courier
```

---

## Production Deployment

For production deployment:

1. **Use production images:**
```bash
   docker build -f pourtier/Dockerfile --target production -t pourtier:production .
```

2. **Use production configs:**
```bash
   docker-compose -f docker-compose.production.yaml up -d
```

3. **Set production environment variables:**
```bash
   cp .env.production .env
   # Edit .env with production secrets
```

4. **Enable systemd service:**
```bash
   sudo systemctl enable lumiere
   sudo systemctl start lumiere
```

---

## References

- **Docker Documentation:** https://docs.docker.com/compose/
- **Docker Networking:** https://docs.docker.com/network/
- **Service Discovery Patterns:** https://microservices.io/patterns/service-registry.html
- **Project Structure:** See `COMPONENT_STANDARD.md`
- **Port Allocation:** See `PORTS.md`

---

## Summary

**Service Discovery in Lumière:**

- Uses Docker DNS (no external dependencies)
- All services in `lumiere-network`
- Automatic service resolution and load balancing
- Config-driven URLs (YAML + env vars)
- Health checks ensure proper startup order
- Easy to scale and monitor
- Works seamlessly in dev, staging, and production

**Status:** Fully implemented and tested

**Last Updated:** October 17, 2025

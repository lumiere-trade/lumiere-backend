# Lumiere Port Allocation

**Configuration Management:** All ports are centrally managed in `ports.yaml`  
**Sync Tool:** `python scripts/update_ports.py`

## Port Scheme
```
PRODUCTION (8xxx - public facing):
  Pourtier:  8000
  Courier:   8765
  Passeur:   8766

DEVELOPMENT (9xxx - local development):
  Pourtier:  9000
  Courier:   9765
  Passeur:   9766

TEST (7xxx - integration/e2e tests):
  Pourtier:  7000
  Courier:   7765
  Passeur:   7766
```

## Architecture

**Single Source of Truth:** `ports.yaml` defines all port allocations.

**Configuration Flow:**
```
ports.yaml (SSOT)
    ↓
scripts/update_ports.py (sync tool)
    ↓
component/config/*.yaml (auto-updated)
    ↓
Services read from config files
```

**Port Mapping Strategy:**
- Each environment uses different container ports (8xxx, 9xxx, 7xxx)
- Docker port mappings are 1:1 (host:container same port)
- Allows parallel execution of all environments simultaneously

## Production Ports (8xxx range)

| Port | Component | Service | Config File |
|------|-----------|---------|-------------|
| 8000 | Pourtier | User Management API | pourtier/config/production.yaml |
| 8765 | Courier | Event Bus (WebSocket) | courier/config/production.yaml |
| 8766 | Passeur | Blockchain Bridge | passeur/config/production.yaml |

## Development Ports (9xxx range)

| Port | Component | Service | Config File |
|------|-----------|---------|-------------|
| 9000 | Pourtier Dev | User Management API | pourtier/config/development.yaml |
| 9765 | Courier Dev | Event Bus (WebSocket) | courier/config/development.yaml |
| 9766 | Passeur Dev | Blockchain Bridge | passeur/config/development.yaml |

## Test Ports (7xxx range)

| Port | Component | Service | Usage |
|------|-----------|---------|-------|
| 7000 | Pourtier Test | User Management API | Integration/E2E tests |
| 7765 | Courier Test | Event Bus (WebSocket) | E2E tests |
| 7766 | Passeur Test | Blockchain Bridge | E2E tests |
| 5433 | PostgreSQL Test | Test Database | Integration/E2E tests |

## Infrastructure Ports

| Port | Service | Purpose | Status |
|------|---------|---------|--------|
| 5432 | PostgreSQL | Database | Running |
| 6379 | Redis | Cache | Running |
| 8086 | InfluxDB | Time-series database | Running |
| 9001 | PyPI Registry (Nginx) | Private Python packages | Running |

## Port Configuration Management

### Checking Consistency

Verify all configs match ports.yaml:
```bash
python scripts/update_ports.py --check
```

### Updating Configuration

When you change ports.yaml, sync all config files:
```bash
# Preview changes
python scripts/update_ports.py --dry-run

# Apply changes
python scripts/update_ports.py
```

### Modifying Ports

**NEVER edit config files directly for port changes.**

Instead:
```bash
# 1. Edit ports.yaml
vim ports.yaml

# 2. Sync configurations
python scripts/update_ports.py

# 3. Verify consistency
python scripts/update_ports.py --check

# 4. Commit changes
git add ports.yaml */config/*.yaml
git commit -m "Update port allocation"
```

## Port Allocation Rules

1. **Production services:** 8000-8799
2. **Development services:** 9000-9799
3. **Test services:** 7000-7799
4. **Infrastructure:** 5000-6999, 8080, 9001+
5. **Always update ports.yaml** - never hardcode ports elsewhere

## Docker Port Mapping

### Internal vs External Ports

Services listen on their configured port (from config YAML):
- Production: Services listen on 8xxx
- Development: Services listen on 9xxx
- Test: Services listen on 7xxx

Docker maps these 1:1 to host:
```yaml
# docker-compose.development.yaml
pourtier:
  ports:
    - "9000:9000"  # host 9000 -> container 9000
```

### Service Discovery (Docker DNS)

Services communicate using Docker DNS with container ports:
```yaml
# development.yaml
courier_url: "http://courier:9765"  # Uses container port
```

Access from host uses mapped port:
```bash
# From host machine
curl http://localhost:9000/health  # Uses host-mapped port
```

## Benefits of This Scheme

- **Parallel Execution:** Run production, development, and tests simultaneously
- **Clear Separation:** Port number indicates environment
- **Safety:** Impossible to confuse prod/dev/test
- **Centralized Management:** Single source of truth for all ports
- **Consistency:** Automatic sync prevents configuration drift

## Checking Active Ports
```bash
# Check all Lumiere ports
sudo lsof -i -P | grep LISTEN | grep -E ":(7|8|9)[0-9]{3}"

# Check specific port
sudo lsof -i :9000
```

## Troubleshooting

### Port already in use
```bash
# Find what's using the port
sudo lsof -i :9000

# Kill the process (if needed)
sudo kill -9 <PID>
```

### Config out of sync
```bash
# Check for mismatches
python scripts/update_ports.py --check

# Fix mismatches
python scripts/update_ports.py
```

### Docker container not accessible
```bash
# Check container is running
docker ps | grep pourtier

# Check port mapping
docker port lumiere-pourtier

# Check logs
docker logs lumiere-pourtier

# Verify healthcheck
docker inspect lumiere-pourtier --format='{{.State.Health.Status}}'
```

## Notes

- All port configuration managed via `ports.yaml`
- Docker DNS uses container ports for service discovery
- External access uses host-mapped ports
- Never hardcode ports in code - always use configuration
- Run `python scripts/update_ports.py --check` in CI/CD to catch drift

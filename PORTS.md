# Lumiere Port Allocation

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

## Port Allocation Rules

1. **Production services:** 8000-8799
2. **Development services:** 9000-9799
3. **Test services:** 7000-7799
4. **Infrastructure:** 5000-6999, 8080, 9001+
5. Always update this file when adding new services

## Benefits of This Scheme

✅ **Parallel Execution:** Run production, development, and tests simultaneously
✅ **Clear Separation:** Port number indicates environment
✅ **Safety:** Impossible to confuse prod/dev/test
✅ **Flexibility:** Test production builds locally without conflicts

## Checking Active Ports
```bash
# Check all Lumiere ports
sudo lsof -i -P | grep LISTEN | grep -E ":(7|8|9)[0-9]{3}"
```

## Notes

- Internal Docker DNS always uses container ports (not external mapped ports)
- Service discovery uses container names: `http://pourtier:9000` (development)
- External access uses mapped ports: `localhost:9000` → container `9000`

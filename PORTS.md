# Lumiere Port Allocation

## Production Ports (8xxx range)

| Port | Component | Service | Config File |
|------|-----------|---------|-------------|
| 8000 | Pourtier | User Management API | pourtier/config/production.yaml |
| 8765 | Courier | Event Bus (WebSocket) | courier/config/production.yaml |
| 8766 | Passeur | Blockchain Bridge | passeur/config/production.yaml |

## Development Ports

| Port | Component | Service | Config File |
|------|-----------|---------|-------------|
| 9000 | Pourtier Dev | User Management API (running) | pourtier/config/development.yaml |
| 8766 | Courier Dev | Event Bus (WebSocket) | courier/config/development.yaml |

## Infrastructure Ports

| Port | Service | Purpose | Status |
|------|---------|---------|--------|
| 5432 | PostgreSQL | Database | Running |
| 6379 | Redis | Cache | Running |
| 8086 | InfluxDB | Time-series database | Running |
| 9001 | PyPI Registry (Nginx) | Private Python packages | Running |

## Documentation

| Port | Service | Purpose |
|------|---------|---------|
| 8080 | MkDocs | Documentation server | - |

## Reserved Ports

| Port Range | Purpose |
|------------|---------|
| 8800-8899 | Future microservices |
| 9002-9099 | Infrastructure services |

## Port Allocation Rules

1. **Production services:** 8000-8799
2. **Development services:** 9000+ (or check development.yaml)
3. **Infrastructure:** 9000-9099
4. **Documentation:** 8080
5. Always update this file when adding new services

## Current Running Services
```bash
# Check all Lumiere ports
sudo lsof -i -P | grep LISTEN | grep -E ":(8|9)[0-9]{3}"
```

## Notes

- Pourtier development currently on port 9000 (process 2724215)
- PyPI Registry on port 9001 (Nginx)
- Courier production on port 8765 (process 2916240)

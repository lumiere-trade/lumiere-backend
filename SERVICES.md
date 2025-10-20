# Lumiere System Services

## Development Environment

Start/stop entire development stack:
```bash
sudo systemctl start lumiere-dev
sudo systemctl stop lumiere-dev
sudo systemctl status lumiere-dev
```

Manages (via `docker-compose.development.yaml`):
- PostgreSQL (internal only, no external port)
- Pourtier API (port 9000)
- Courier WebSocket (port 9765)
- Passeur Bridge (port 9766)

## Test Environment

Start/stop test stack (for E2E testing):
```bash
sudo systemctl start lumiere-test
sudo systemctl stop lumiere-test
sudo systemctl status lumiere-test
```

Manages (via `docker-compose.test.yaml`):
- PostgreSQL (port 5433:5432)
- Pourtier API (port 7000)
- Courier WebSocket (port 7765)
- Passeur Bridge (port 7766)

## Production Environment

Start/stop production stack:
```bash
sudo systemctl start lumiere
sudo systemctl stop lumiere
sudo systemctl status lumiere
```

Manages (via `docker-compose.production.yaml`):
- PostgreSQL (internal only)
- Pourtier API (port 8000)
- Courier WebSocket (port 8765)
- Passeur Bridge (port 8766)

## Port Allocation Summary

| Service  | Production | Development | Test |
|----------|------------|-------------|------|
| Pourtier | 8000       | 9000        | 7000 |
| Courier  | 8765       | 9765        | 7765 |
| Passeur  | 8766       | 9766        | 7766 |
| Postgres | internal   | internal    | 5433 |

See `ports.yaml` for authoritative port allocation.

## Manual Docker Compose

Alternatively, manage manually:
```bash
# Development
docker-compose -f docker-compose.development.yaml up -d
docker-compose -f docker-compose.development.yaml down

# Test
docker-compose -f docker-compose.test.yaml --profile integration --profile e2e up -d
docker-compose -f docker-compose.test.yaml down

# Production
docker-compose -f docker-compose.production.yaml up -d
docker-compose -f docker-compose.production.yaml down
```

## Notes

- Only enable services you actively use: `sudo systemctl enable lumiere-dev`
- Development is typically the only enabled service
- Test and production are started manually as needed
- All services use Docker networks for internal communication
- External ports are only exposed where necessary

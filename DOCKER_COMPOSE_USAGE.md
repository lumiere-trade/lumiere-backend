# Docker Compose Usage Guide

## Development Environment

Start development stack with 9xxx ports:
```bash
# Start all services
docker compose -f docker-compose.development.yaml up -d

# View logs
docker compose -f docker-compose.development.yaml logs -f

# Stop services
docker compose -f docker-compose.development.yaml down

# Stop and remove volumes
docker compose -f docker-compose.development.yaml down -v
```

## Production Environment

Start production stack with 8xxx ports:
```bash
# Start all services
docker compose -f docker-compose.production.yaml up -d

# View logs
docker compose -f docker-compose.production.yaml logs -f

# Stop services
docker compose -f docker-compose.production.yaml down
```

## Test Environment

### Integration Tests

Start only services needed for integration tests (pourtier + postgres):
```bash
# Start integration profile
docker compose -f docker-compose.test.yaml --profile integration up -d

# Run tests
laborant test pourtier --integration

# Cleanup
docker compose -f docker-compose.test.yaml down -v
```

### E2E Tests

Start full stack for end-to-end tests:
```bash
# Start e2e profile (all services)
docker compose -f docker-compose.test.yaml --profile e2e up -d

# Run tests
laborant test pourtier --e2e

# Cleanup
docker compose -f docker-compose.test.yaml down -v
```

## Shell Aliases (Optional)

Add to ~/.bashrc or ~/.zshrc:
```bash
alias dc-dev='docker compose -f docker-compose.development.yaml'
alias dc-prod='docker compose -f docker-compose.production.yaml'
alias dc-test='docker compose -f docker-compose.test.yaml'
```

Usage examples:
```bash
dc-dev up -d
dc-dev logs -f pourtier
dc-dev down

dc-test --profile integration up -d
dc-test down -v
```

## Port Reference

| Environment | Pourtier | Courier | Passeur | Postgres |
|-------------|----------|---------|---------|----------|
| Development | 9000     | 9765    | 9766    | internal |
| Production  | 8000     | 8765    | 8766    | internal |
| Test        | 7000     | 7765    | 7766    | 5433     |

## Troubleshooting

Check running containers:
```bash
docker ps
```

Check all containers (including stopped):
```bash
docker ps -a
```

View specific service logs:
```bash
docker compose -f docker-compose.development.yaml logs pourtier
```

Rebuild specific service:
```bash
docker compose -f docker-compose.development.yaml build pourtier
docker compose -f docker-compose.development.yaml up -d pourtier
```

Remove all stopped containers and unused images:
```bash
docker system prune -a
```

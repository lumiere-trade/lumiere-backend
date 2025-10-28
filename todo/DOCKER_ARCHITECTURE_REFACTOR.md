# Docker Architecture Refactor Task

## Problem Statement

The current Docker Compose architecture violates Clean Architecture and microservices principles by using shared, monolithic docker-compose files at the project root level. This creates tight coupling between components and prevents independent deployment and testing.

## Current Architecture (INCORRECT)
```
lumiere-backend/
├── docker-compose.development.yaml   # ❌ Shared infrastructure for ALL components
├── docker-compose.test.yaml          # ❌ Mixed test infrastructure
├── docker-compose.production.yaml    # ❌ Monolithic deployment
├── pourtier/
│   ├── Dockerfile
│   ├── src/
│   └── tests/
├── courier/
│   ├── Dockerfile
│   ├── src/
│   └── tests/
├── passeur/
│   ├── Dockerfile
│   ├── src/
│   └── tests/
└── [other components...]
```

### Current Docker Compose Files

**docker-compose.test.yaml** (example structure):
```yaml
services:
  postgres-test:
    image: postgres:16
    environment:
      POSTGRES_DB: lumiere_test
      POSTGRES_USER: lumiere
      POSTGRES_PASSWORD: test_password
    profiles: ["integration", "e2e"]

  pourtier-test:
    build:
      context: .
      dockerfile: pourtier/Dockerfile
    depends_on:
      - postgres-test
    profiles: ["integration", "e2e"]

  courier-test:
    build:
      context: .
      dockerfile: courier/Dockerfile
    profiles: ["integration", "e2e"]  # ❌ Courier doesn't need Docker!

  passeur-test:
    build:
      context: .
      dockerfile: passeur/Dockerfile
    profiles: ["integration", "e2e"]
```

### Problems with Current Architecture

1. **Tight Coupling**: All components share the same infrastructure configuration
2. **No Independent Deployment**: Cannot deploy/test one component without affecting others
3. **Unclear Dependencies**: Not obvious which components need which services
4. **Inefficient Testing**: Courier integration tests forced into Docker unnecessarily
5. **Monolithic Thinking**: Defeats the purpose of microservices architecture
6. **Difficult Maintenance**: Changes to one component's infrastructure affects all others
7. **Poor Scalability**: Cannot scale individual components independently

## Target Architecture (CORRECT)
```
lumiere-backend/
├── pourtier/
│   ├── docker-compose.yaml           # ✅ Pourtier-specific infrastructure
│   ├── docker-compose.test.yaml      # ✅ Pourtier test infrastructure
│   ├── Dockerfile
│   ├── src/
│   └── tests/
├── courier/
│   ├── Dockerfile                    # ✅ No docker-compose (no DB needed)
│   ├── src/
│   └── tests/                        # ✅ Runs on host (fast, no overhead)
├── passeur/
│   ├── docker-compose.yaml           # ✅ Passeur-specific infrastructure
│   ├── docker-compose.test.yaml      # ✅ Passeur test infrastructure
│   ├── Dockerfile
│   ├── src/
│   └── tests/
└── [other components with their own docker-compose files...]
```

### Example: Pourtier Component Structure

**pourtier/docker-compose.yaml** (Development):
```yaml
services:
  postgres:
    image: postgres:16
    container_name: pourtier-postgres-dev
    environment:
      POSTGRES_DB: pourtier_dev
      POSTGRES_USER: lumiere
      POSTGRES_PASSWORD: dev_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_dev_data:/var/lib/postgresql/data

  pourtier:
    build:
      context: .
      dockerfile: Dockerfile
      target: development
    container_name: pourtier-dev
    ports:
      - "9000:8000"
    depends_on:
      - postgres
    environment:
      DATABASE_URL: postgresql://lumiere:dev_password@postgres:5432/pourtier_dev
    volumes:
      - ./src:/app/src
      - ./tests:/app/tests

volumes:
  postgres_dev_data:
```

**pourtier/docker-compose.test.yaml** (Testing):
```yaml
services:
  postgres-test:
    image: postgres:16
    container_name: pourtier-postgres-test
    environment:
      POSTGRES_DB: pourtier_test
      POSTGRES_USER: lumiere
      POSTGRES_PASSWORD: test_password
    ports:
      - "5433:5432"
    tmpfs:
      - /var/lib/postgresql/data  # In-memory for faster tests

  pourtier-test:
    build:
      context: .
      dockerfile: Dockerfile
      target: development
    container_name: pourtier-test
    depends_on:
      - postgres-test
    environment:
      DATABASE_URL: postgresql://lumiere:test_password@postgres-test:5432/pourtier_test
      ENV: test
    volumes:
      - ./tests:/app/tests
```

### Example: Courier Component Structure

**courier/** (NO docker-compose needed):
```
courier/
├── Dockerfile                        # Only Dockerfile for production deployment
├── src/
│   └── courier/
│       ├── domain/
│       ├── application/
│       └── infrastructure/
└── tests/
    ├── unit/                         # Runs on host
    ├── integration/                  # Runs on host (no DB needed!)
    │   ├── infrastructure/
    │   │   ├── test_jwt_verifier.py
    │   │   └── test_connection_manager.py
    │   └── api/
    │       └── test_websocket_routes.py
    └── e2e/                          # Would need Docker if we add e2e tests
```

## Benefits of Target Architecture

### 1. Clear Separation of Concerns
- Each component owns its infrastructure
- Easy to see which components need databases/services
- Courier clearly has no docker-compose = no external dependencies

### 2. Independent Development
```bash
# Work on Pourtier only
cd pourtier
docker compose up -d

# Work on Passeur only
cd passeur
docker compose up -d

# No docker-compose for Courier - just run tests
cd courier
python tests/integration/infrastructure/test_jwt_verifier.py
```

### 3. Independent Testing
```bash
# Test Pourtier with its DB
cd pourtier
docker compose -f docker-compose.test.yaml up -d
laborant test pourtier --integration
docker compose -f docker-compose.test.yaml down -v

# Test Courier on host (fast!)
cd courier
laborant test courier --integration  # Runs on host, no Docker overhead

# Test Passeur with blockchain
cd passeur
docker compose -f docker-compose.test.yaml up -d
laborant test passeur --integration
docker compose -f docker-compose.test.yaml down -v
```

### 4. Independent Deployment
```bash
# Deploy only Pourtier
cd pourtier
docker build -t pourtier:latest .
docker compose -f docker-compose.production.yaml up -d

# Deploy only Courier
cd courier
docker build -t courier:latest .
docker run -p 8765:8765 courier:latest  # No compose needed!
```

### 5. Clear Dependencies
- `ls pourtier/docker-compose.yaml` → "Ah, Pourtier needs PostgreSQL"
- `ls courier/` → "No docker-compose? Courier has no external dependencies!"
- `ls passeur/docker-compose.yaml` → "Passeur needs blockchain services"

## Migration Steps

### Phase 1: Analyze Current Setup

1. **Document current docker-compose files**:
```bash
cat docker-compose.test.yaml > todo/current-docker-compose-test.yaml
cat docker-compose.development.yaml > todo/current-docker-compose-dev.yaml
cat docker-compose.production.yaml > todo/current-docker-compose-prod.yaml
```

2. **Identify dependencies per component**:
   - Pourtier: PostgreSQL, Redis (optional)
   - Passeur: Solana RPC, PostgreSQL (maybe)
   - Courier: NONE (just WebSocket server)
   - Architect: Database (TBD)
   - Prophet: AI services (TBD)
   - Cartographe: Database, Market data (TBD)

### Phase 2: Create Component-Level Docker Compose Files

#### For Pourtier:

1. **Create `pourtier/docker-compose.yaml`**:
```bash
cd pourtier
cat > docker-compose.yaml << 'YAML'
services:
  postgres:
    image: postgres:16
    container_name: pourtier-postgres-dev
    environment:
      POSTGRES_DB: pourtier_dev
      POSTGRES_USER: lumiere
      POSTGRES_PASSWORD: dev_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_dev_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U lumiere"]
      interval: 5s
      timeout: 5s
      retries: 5

  pourtier:
    build:
      context: .
      dockerfile: Dockerfile
      target: development
    container_name: pourtier-dev
    ports:
      - "9000:8000"
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      DATABASE_URL: postgresql://lumiere:dev_password@postgres:5432/pourtier_dev
      ENV: development
    volumes:
      - ./src:/app/src
      - ./tests:/app/tests
      - ./config:/app/config

volumes:
  postgres_dev_data:
YAML
```

2. **Create `pourtier/docker-compose.test.yaml`**:
```bash
cat > docker-compose.test.yaml << 'YAML'
services:
  postgres-test:
    image: postgres:16
    container_name: pourtier-postgres-test
    environment:
      POSTGRES_DB: pourtier_test
      POSTGRES_USER: lumiere
      POSTGRES_PASSWORD: test_password
    ports:
      - "5433:5432"
    tmpfs:
      - /var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U lumiere"]
      interval: 2s
      timeout: 2s
      retries: 5

  pourtier-test:
    build:
      context: .
      dockerfile: Dockerfile
      target: development
    container_name: pourtier-test
    depends_on:
      postgres-test:
        condition: service_healthy
    environment:
      DATABASE_URL: postgresql://lumiere:test_password@postgres-test:5432/pourtier_test
      ENV: test
    volumes:
      - ./tests:/app/tests

volumes:
  postgres_test_data:
YAML
```

3. **Create `pourtier/Makefile`** for convenience:
```bash
cat > Makefile << 'MAKE'
.PHONY: dev test clean

dev:
	docker compose up -d
	@echo "Pourtier development environment started"
	@echo "API: http://localhost:9000"
	@echo "Database: postgresql://lumiere:dev_password@localhost:5432/pourtier_dev"

test:
	docker compose -f docker-compose.test.yaml up -d
	@echo "Waiting for database..."
	sleep 3
	laborant test pourtier --integration
	docker compose -f docker-compose.test.yaml down -v

logs:
	docker compose logs -f

clean:
	docker compose down -v
	docker compose -f docker-compose.test.yaml down -v

.DEFAULT_GOAL := dev
MAKE
```

#### For Courier:

**NO docker-compose.yaml needed!** Courier has no external dependencies.

1. **Create `courier/Makefile`**:
```bash
cd ../courier
cat > Makefile << 'MAKE'
.PHONY: test dev clean

dev:
	@echo "Courier has no docker-compose - runs directly"
	@echo "Start with: uvicorn courier.main:app --reload --port 9765"

test:
	@echo "Running Courier integration tests on host (fast!)"
	laborant test courier --integration

test-unit:
	laborant test courier --unit

.DEFAULT_GOAL := test
MAKE
```

#### For Passeur:

Similar to Pourtier, create component-specific docker-compose files based on its dependencies.

### Phase 3: Update Laborant to Use Component-Level Compose Files

**Update `laborant/src/laborant/core/docker_test_executor.py`**:

Current logic looks for `docker-compose.test.yaml` at project root.
New logic should look for `<component>/docker-compose.test.yaml`.
```python
def _get_compose_file_path(self, component: str) -> Optional[Path]:
    """
    Get docker-compose test file for component.
    
    Args:
        component: Component name
        
    Returns:
        Path to docker-compose.test.yaml or None if doesn't exist
    """
    component_path = self.project_root / component
    compose_file = component_path / "docker-compose.test.yaml"
    
    if compose_file.exists():
        return compose_file
    
    # Fallback to old location (during migration)
    old_location = self.project_root / "docker-compose.test.yaml"
    if old_location.exists():
        self.reporter.warning(
            f"Using deprecated docker-compose at project root for {component}",
            context="DockerTestExecutor"
        )
        return old_location
    
    return None

def ensure_infrastructure(self, component: Optional[str] = None) -> bool:
    """Start Docker infrastructure for component."""
    if self._infrastructure_started:
        return True
    
    if not component:
        self.reporter.error(
            "Component name required for Docker infrastructure",
            context="DockerTestExecutor"
        )
        return False
    
    compose_file = self._get_compose_file_path(component)
    
    if not compose_file:
        self.reporter.warning(
            f"No docker-compose.test.yaml found for {component}",
            context="DockerTestExecutor"
        )
        return False
    
    try:
        # Start infrastructure for this component only
        subprocess.run(
            [
                "docker",
                "compose",
                "-f",
                str(compose_file),
                "up",
                "-d",
            ],
            cwd=str(compose_file.parent),  # Run from component directory
            check=True,
            capture_output=True,
            text=True,
        )
        
        self._infrastructure_started = True
        self.reporter.info(
            f"Started Docker infrastructure for {component}",
            context="DockerTestExecutor"
        )
        return True
        
    except subprocess.CalledProcessError as e:
        self.reporter.error(
            f"Failed to start Docker infrastructure: {e.stderr}",
            context="DockerTestExecutor"
        )
        return False
```

### Phase 4: Update `_component_needs_docker()` Logic

Since each component will have its own docker-compose.test.yaml (or not), update the check:
```python
def _component_needs_docker(self, component_name: str, category: str) -> bool:
    """
    Check if component needs Docker for given test category.
    
    Component needs Docker if it has docker-compose.test.yaml file.
    
    Args:
        component_name: Component name
        category: Test category
        
    Returns:
        True if Docker needed, False otherwise
    """
    # E2E tests always need Docker
    if category == "e2e":
        return True
    
    # Check for component-level docker-compose.test.yaml
    component_path = self.project_root / component_name
    compose_file = component_path / "docker-compose.test.yaml"
    
    if compose_file.exists():
        self.reporter.debug(
            f"{component_name} has docker-compose.test.yaml - needs Docker",
            context="Laborant"
        )
        return True
    
    # No docker-compose = can run on host
    self.reporter.debug(
        f"{component_name} has no docker-compose.test.yaml - runs on host",
        context="Laborant"
    )
    return False
```

### Phase 5: Testing Migration

1. **Test Pourtier with new compose files**:
```bash
cd pourtier
docker compose -f docker-compose.test.yaml up -d
laborant test pourtier --integration
docker compose -f docker-compose.test.yaml down -v
```

2. **Test Courier on host**:
```bash
cd courier
laborant test courier --integration  # Should detect no docker-compose and run on host
```

3. **Verify Laborant smart detection**:
```bash
cd ~/lumiere/lumiere-backend
laborant test courier --integration  # Host
laborant test pourtier --integration  # Docker
```

### Phase 6: Cleanup Old Files

Once migration is verified working:
```bash
cd ~/lumiere/lumiere-backend
git mv docker-compose.test.yaml todo/old-docker-compose.test.yaml
git mv docker-compose.development.yaml todo/old-docker-compose.development.yaml
git mv docker-compose.production.yaml todo/old-docker-compose.production.yaml
```

## Rollback Plan

If migration causes issues:

1. Keep old docker-compose files in `todo/` directory
2. Add fallback logic in Laborant to use old files if component-level missing
3. Gradual migration: one component at a time

## Success Criteria

✅ Each component has its own docker-compose files (if needed)
✅ Courier has NO docker-compose (runs on host)
✅ Pourtier integration tests work with component-level docker-compose.test.yaml
✅ Laborant correctly detects which components need Docker
✅ Can start/test each component independently
✅ Old root-level docker-compose files archived or deleted
✅ Documentation updated (README, DOCKER_COMPOSE_USAGE.md)

## Timeline Estimate

- Phase 1 (Analysis): 30 minutes
- Phase 2 (Create component compose files): 2 hours
- Phase 3 (Update Laborant): 1 hour
- Phase 4 (Update detection logic): 30 minutes
- Phase 5 (Testing): 1 hour
- Phase 6 (Cleanup): 30 minutes

**Total: ~5-6 hours**

## Priority

🔴 **HIGH PRIORITY**

This architectural debt will compound as more components are added. Better to fix now before the codebase grows larger.

## Related Files to Update

- `laborant/src/laborant/core/orchestrator.py` - Smart executor selection
- `laborant/src/laborant/core/docker_test_executor.py` - Compose file detection
- `docs/DOCKER_COMPOSE_USAGE.md` - Usage documentation
- Each component `README.md` - Local development instructions

## Notes

- This refactor aligns with Clean Architecture principles
- Follows microservices best practices
- Makes testing significantly faster for lightweight components like Courier
- Reduces cognitive load - clear which components need what infrastructure
- Enables true independent deployment and scaling

---

**Created**: 2025-10-28
**Status**: TODO
**Assigned**: AI Assistant / Vladimir
**Estimated Effort**: 5-6 hours

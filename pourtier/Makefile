# =============================================
# POURTIER COMPONENT MAKEFILE
# Manages: Docker images + Infrastructure (Postgres + Pourtier)
# =============================================

.PHONY: help build-dev build-prod run-dev run-prod clean
.PHONY: dev dev-logs dev-stop dev-restart dev-clean
.PHONY: test test-logs test-stop test-clean
.PHONY: prod prod-logs prod-stop prod-restart prod-clean

COMPONENT = pourtier
PORT_DEV = 9000
PORT_PROD = 8000
PORT_TEST = 7000
PROJECT_ROOT = ..

# Colors
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
RED := \033[0;31m
NC := \033[0m

# =============================================
# HELP
# =============================================

help:
	@echo "$(GREEN)╔═══════════════════════════════════════════╗$(NC)"
	@echo "$(GREEN)║   POURTIER COMPONENT MANAGEMENT           ║$(NC)"
	@echo "$(GREEN)╚═══════════════════════════════════════════╝$(NC)"
	@echo ""
	@echo "$(YELLOW)Image Building:$(NC)"
	@echo "  make build-dev      - Build development image"
	@echo "  make build-prod     - Build production image"
	@echo ""
	@echo "$(YELLOW)Development Environment (port $(PORT_DEV)):$(NC)"
	@echo "  make dev            - Start dev infrastructure (Postgres + Pourtier)"
	@echo "  make dev-logs       - Show dev logs (follow)"
	@echo "  make dev-stop       - Stop dev environment"
	@echo "  make dev-restart    - Restart dev environment"
	@echo "  make dev-clean      - Stop and remove dev volumes"
	@echo ""
	@echo "$(YELLOW)Test Environment (port $(PORT_TEST)):$(NC)"
	@echo "  make test           - Start test infrastructure"
	@echo "  make test-logs      - Show test logs"
	@echo "  make test-stop      - Stop test environment"
	@echo "  make test-clean     - Stop and remove test volumes"
	@echo ""
	@echo "$(YELLOW)Production Environment (port $(PORT_PROD)):$(NC)"
	@echo "  make prod           - Start prod infrastructure"
	@echo "  make prod-logs      - Show prod logs"
	@echo "  make prod-stop      - Stop prod environment"
	@echo "  make prod-restart   - Restart prod environment"
	@echo "  make prod-clean     - Stop and remove prod volumes"
	@echo ""
	@echo "$(YELLOW)Standalone Container (legacy):$(NC)"
	@echo "  make run-dev        - Run dev container only (no Postgres)"
	@echo "  make run-prod       - Run prod container only (no Postgres)"
	@echo ""
	@echo "$(YELLOW)Cleanup:$(NC)"
	@echo "  make clean          - Remove all Docker images"
	@echo "  make clean-all      - Remove images + all environment volumes"

# =============================================
# IMAGE BUILDING
# =============================================

build-dev:
	@echo "$(BLUE)[BUILD]$(NC) Building $(COMPONENT):development with BuildKit..."
	@echo "$(BLUE)[INFO]$(NC) Using PyPI Registry at http://localhost:9001/simple/"
	cd $(PROJECT_ROOT) && docker buildx build \
		-f $(COMPONENT)/Dockerfile \
		--target development \
		-t $(COMPONENT):development \
		--add-host host.docker.internal:host-gateway \
		--load \
		.
	@echo "$(GREEN)[SUCCESS]$(NC) Built $(COMPONENT):development"

build-prod:
	@echo "$(BLUE)[BUILD]$(NC) Building $(COMPONENT):production with BuildKit..."
	@echo "$(BLUE)[INFO]$(NC) Using PyPI Registry at http://localhost:9001/simple/"
	cd $(PROJECT_ROOT) && docker buildx build \
		-f $(COMPONENT)/Dockerfile \
		--target production \
		-t $(COMPONENT):production \
		--add-host host.docker.internal:host-gateway \
		--load \
		.
	docker tag $(COMPONENT):production $(COMPONENT):latest
	@echo "$(GREEN)[SUCCESS]$(NC) Built $(COMPONENT):production"

# =============================================
# DEVELOPMENT ENVIRONMENT
# =============================================

dev:
	@echo "$(GREEN)[DEV]$(NC) Starting development environment (port $(PORT_DEV))..."
	docker compose -f docker-compose-development.yaml up -d
	@echo "$(GREEN)[SUCCESS]$(NC) Development environment started"
	@echo "$(BLUE)[INFO]$(NC) Pourtier API: http://localhost:$(PORT_DEV)"
	@echo "$(BLUE)[INFO]$(NC) Database: postgres:5432 (internal)"

dev-logs:
	docker compose -f docker-compose-development.yaml logs -f

dev-stop:
	@echo "$(YELLOW)[DEV]$(NC) Stopping development environment..."
	docker compose -f docker-compose-development.yaml down
	@echo "$(GREEN)[SUCCESS]$(NC) Development environment stopped"

dev-restart: dev-stop dev

dev-clean:
	@echo "$(RED)[DEV]$(NC) Stopping and removing development volumes..."
	docker compose -f docker-compose-development.yaml down -v
	@echo "$(GREEN)[SUCCESS]$(NC) Development environment cleaned"

# =============================================
# TEST ENVIRONMENT
# =============================================

test:
	@echo "$(GREEN)[TEST]$(NC) Starting test environment (port $(PORT_TEST))..."
	docker compose -f docker-compose-test.yaml up -d
	@echo "$(GREEN)[SUCCESS]$(NC) Test environment started"
	@echo "$(BLUE)[INFO]$(NC) Pourtier API: http://localhost:$(PORT_TEST)"
	@echo "$(BLUE)[INFO]$(NC) Database: localhost:5433 (external access)"

test-logs:
	docker compose -f docker-compose-test.yaml logs -f

test-stop:
	@echo "$(YELLOW)[TEST]$(NC) Stopping test environment..."
	docker compose -f docker-compose-test.yaml down
	@echo "$(GREEN)[SUCCESS]$(NC) Test environment stopped"

test-clean:
	@echo "$(RED)[TEST]$(NC) Stopping and removing test volumes..."
	docker compose -f docker-compose-test.yaml down -v
	@echo "$(GREEN)[SUCCESS]$(NC) Test environment cleaned"

# =============================================
# PRODUCTION ENVIRONMENT
# =============================================

prod:
	@echo "$(GREEN)[PROD]$(NC) Starting production environment (port $(PORT_PROD))..."
	docker compose -f docker-compose-production.yaml up -d
	@echo "$(GREEN)[SUCCESS]$(NC) Production environment started"
	@echo "$(BLUE)[INFO]$(NC) Pourtier API: http://localhost:$(PORT_PROD)"
	@echo "$(BLUE)[INFO]$(NC) Database: postgres:5432 (internal)"

prod-logs:
	docker compose -f docker-compose-production.yaml logs -f

prod-stop:
	@echo "$(YELLOW)[PROD]$(NC) Stopping production environment..."
	docker compose -f docker-compose-production.yaml down
	@echo "$(GREEN)[SUCCESS]$(NC) Production environment stopped"

prod-restart: prod-stop prod

prod-clean:
	@echo "$(RED)[PROD]$(NC) Stopping and removing production volumes..."
	docker compose -f docker-compose-production.yaml down -v
	@echo "$(GREEN)[SUCCESS]$(NC) Production environment cleaned"

# =============================================
# STANDALONE CONTAINER (Legacy - no Postgres)
# =============================================

run-dev:
	@echo "$(BLUE)[RUN]$(NC) Starting $(COMPONENT):development on port $(PORT_DEV)..."
	@echo "$(YELLOW)[WARNING]$(NC) Running standalone - no Postgres!"
	docker run --rm -p $(PORT_DEV):$(PORT_DEV) \
		--env-file .env.development \
		--add-host host.docker.internal:host-gateway \
		--name $(COMPONENT)-dev \
		$(COMPONENT):development

run-prod:
	@echo "$(BLUE)[RUN]$(NC) Starting $(COMPONENT):production on port $(PORT_PROD)..."
	@echo "$(YELLOW)[WARNING]$(NC) Running standalone - no Postgres!"
	docker run --rm -p $(PORT_PROD):$(PORT_PROD) \
		--env-file .env.production \
		--add-host host.docker.internal:host-gateway \
		--name $(COMPONENT)-prod \
		$(COMPONENT):production

# =============================================
# CLEANUP
# =============================================

clean:
	@echo "$(RED)[CLEAN]$(NC) Removing $(COMPONENT) images..."
	docker rmi $(COMPONENT):development $(COMPONENT):production $(COMPONENT):latest 2>/dev/null || true
	@echo "$(GREEN)[SUCCESS]$(NC) Images cleaned"

clean-all: dev-clean test-clean prod-clean clean
	@echo "$(GREEN)[SUCCESS]$(NC) All environments and images cleaned"

.DEFAULT_GOAL := help

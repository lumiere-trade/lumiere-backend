# Courier Component Makefile
# Build context: courier/ (component-level isolation)

.PHONY: help build-dev build-prod run-dev run-prod clean test

COMPONENT = courier
PORT_DEV = 9765
PORT_PROD = 8765

help:
	@echo "=== Courier Commands ==="
	@echo "make build-dev   - Build development"
	@echo "make build-prod  - Build production"
	@echo "make run-dev     - Run lumiere-dev-courier"
	@echo "make run-prod    - Run lumiere-courier"

build-dev:
	@echo "[BUILD] courier:development (component context)..."
	DOCKER_BUILDKIT=1 docker build \
		-f Dockerfile \
		--target development \
		-t $(COMPONENT):development \
		.

build-prod:
	@echo "[BUILD] courier:production (component context)..."
	DOCKER_BUILDKIT=1 docker build \
		-f Dockerfile \
		--target production \
		-t $(COMPONENT):production \
		.

run-dev:
	@echo "[RUN] lumiere-dev-$(COMPONENT)..."
	docker run -d \
		--name lumiere-dev-$(COMPONENT) \
		-p $(PORT_DEV):$(PORT_DEV) \
		-e ENV=development \
		$(COMPONENT):development

run-prod:
	@echo "[RUN] lumiere-$(COMPONENT)..."
	docker run -d \
		--name lumiere-$(COMPONENT) \
		-p $(PORT_PROD):$(PORT_PROD) \
		-e ENV=production \
		$(COMPONENT):production

clean:
	@echo "[CLEAN] Removing containers and images..."
	docker rm -f lumiere-dev-$(COMPONENT) lumiere-$(COMPONENT) 2>/dev/null || true
	docker rmi -f $(COMPONENT):development $(COMPONENT):production 2>/dev/null || true

stop:
	docker stop lumiere-dev-$(COMPONENT) lumiere-$(COMPONENT) 2>/dev/null || true

logs-dev:
	docker logs -f lumiere-dev-$(COMPONENT)

logs-prod:
	docker logs -f lumiere-$(COMPONENT)

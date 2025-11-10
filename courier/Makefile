# Courier Component Makefile

.PHONY: help build-dev build-prod run-dev run-prod clean test

COMPONENT = courier
PORT_DEV = 9765
PORT_PROD = 8765
PROJECT_ROOT = ..

help:
	@echo "=== Courier Docker Commands ==="
	@echo "make build-dev   - Build development image"
	@echo "make build-prod  - Build production image"
	@echo "make run-dev     - Run lumiere-dev-courier"
	@echo "make run-prod    - Run lumiere-courier"
	@echo "make test        - Test the container"
	@echo "make clean       - Remove images and containers"

build-dev:
	@echo "[BUILD] Building $(COMPONENT):development..."
	cd $(PROJECT_ROOT) && \
	DOCKER_BUILDKIT=1 docker buildx build \
		-f $(COMPONENT)/Dockerfile \
		--target development \
		--tag $(COMPONENT):development \
		--load \
		--progress=plain \
		.

build-prod:
	@echo "[BUILD] Building $(COMPONENT):production..."
	cd $(PROJECT_ROOT) && \
	DOCKER_BUILDKIT=1 docker buildx build \
		-f $(COMPONENT)/Dockerfile \
		--target production \
		--tag $(COMPONENT):production \
		--load \
		--progress=plain \
		.

run-dev:
	@echo "[RUN] Starting lumiere-dev-$(COMPONENT)..."
	docker run -d \
		--name lumiere-dev-$(COMPONENT) \
		--network lumiere-network \
		-p $(PORT_DEV):$(PORT_DEV) \
		-e ENV=development \
		-e DEBUG=true \
		--restart unless-stopped \
		$(COMPONENT):development

run-prod:
	@echo "[RUN] Starting lumiere-$(COMPONENT)..."
	docker run -d \
		--name lumiere-$(COMPONENT) \
		--network lumiere-network \
		-p $(PORT_PROD):$(PORT_PROD) \
		-e ENV=production \
		--restart unless-stopped \
		$(COMPONENT):production

test:
	@echo "[TEST] Testing $(COMPONENT)..."
	curl -f http://localhost:$(PORT_DEV)/health || echo "Health check failed"

clean:
	@echo "[CLEAN] Removing $(COMPONENT) containers and images..."
	docker rm -f lumiere-dev-$(COMPONENT) lumiere-$(COMPONENT) 2>/dev/null || true
	docker rmi -f $(COMPONENT):development $(COMPONENT):production 2>/dev/null || true
	docker builder prune -f

stop:
	@echo "[STOP] Stopping $(COMPONENT) containers..."
	docker stop lumiere-dev-$(COMPONENT) lumiere-$(COMPONENT) 2>/dev/null || true

logs-dev:
	@echo "[LOGS] Development logs..."
	docker logs -f lumiere-dev-$(COMPONENT)

logs-prod:
	@echo "[LOGS] Production logs..."
	docker logs -f lumiere-$(COMPONENT)

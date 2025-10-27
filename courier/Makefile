# Courier Component Makefile

.PHONY: help build-dev build-prod run-dev run-prod clean test

COMPONENT = courier
PORT_DEV = 9765
PORT_PROD = 8765
PROJECT_ROOT = ..

help:
	@echo "=== Courier Docker Commands ==="
	@echo "make build-dev   - Build development image with buildx"
	@echo "make build-prod  - Build production image with buildx"
	@echo "make run-dev     - Run development container"
	@echo "make run-prod    - Run production container"
	@echo "make test        - Test the container"
	@echo "make clean       - Remove images and builder"

build-dev:
	@echo "[BUILD] Building $(COMPONENT):development with buildx..."
	@echo "[INFO] Using PyPI Registry at http://localhost:9001/simple/"
	cd $(PROJECT_ROOT) && \
	DOCKER_BUILDKIT=1 docker buildx build \
		-f $(COMPONENT)/Dockerfile \
		--target development \
		--tag $(COMPONENT):development \
		--load \
		--progress=plain \
		.

build-prod:
	@echo "[BUILD] Building $(COMPONENT):production with buildx..."
	@echo "[INFO] Using PyPI Registry at http://localhost:9001/simple/"
	cd $(PROJECT_ROOT) && \
	DOCKER_BUILDKIT=1 docker buildx build \
		-f $(COMPONENT)/Dockerfile \
		--target production \
		--tag $(COMPONENT):production \
		--load \
		--progress=plain \
		.

run-dev:
	@echo "[RUN] Starting $(COMPONENT) development container..."
	docker run -d \
		--name $(COMPONENT)-dev \
		--network lumiere-network \
		-p $(PORT_DEV):$(PORT_DEV) \
		-e ENV=development \
		-e DEBUG=true \
		--restart unless-stopped \
		$(COMPONENT):development

run-prod:
	@echo "[RUN] Starting $(COMPONENT) production container..."
	docker run -d \
		--name $(COMPONENT)-prod \
		--network lumiere-network \
		-p $(PORT_PROD):$(PORT_PROD) \
		-e ENV=production \
		--restart unless-stopped \
		$(COMPONENT):production

test:
	@echo "[TEST] Testing $(COMPONENT) container..."
	@echo "[TEST] Health check..."
	curl -f http://localhost:$(PORT_DEV)/health || echo "Health check failed"
	@echo ""
	@echo "[TEST] Stats check..."
	curl -f http://localhost:$(PORT_DEV)/stats || echo "Stats check failed"

clean:
	@echo "[CLEAN] Removing $(COMPONENT) images..."
	docker rm -f $(COMPONENT)-dev $(COMPONENT)-prod 2>/dev/null || true
	docker rmi -f $(COMPONENT):development $(COMPONENT):production 2>/dev/null || true
	@echo "[CLEAN] Cleaning build cache..."
	docker builder prune -f

stop:
	@echo "[STOP] Stopping $(COMPONENT) containers..."
	docker stop $(COMPONENT)-dev $(COMPONENT)-prod 2>/dev/null || true

logs-dev:
	@echo "[LOGS] Development container logs..."
	docker logs -f $(COMPONENT)-dev

logs-prod:
	@echo "[LOGS] Production container logs..."
	docker logs -f $(COMPONENT)-prod

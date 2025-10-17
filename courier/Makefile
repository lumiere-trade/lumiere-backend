# Courier Component Makefile

.PHONY: help build-dev build-prod run-dev run-prod clean

COMPONENT = courier
PORT_DEV = 9765
PORT_PROD = 8765
PROJECT_ROOT = ..

help:
	@echo "=== Courier Docker Commands ==="
	@echo "make build-dev   - Build development image"
	@echo "make build-prod  - Build production image"
	@echo "make run-dev     - Run development container"
	@echo "make run-prod    - Run production container"
	@echo "make clean       - Remove images"

build-dev:
	@echo "[BUILD] Building $(COMPONENT):development with BuildKit..."
	@echo "[INFO] Using PyPI Registry at http://localhost:9001/simple/"
	cd $(PROJECT_ROOT) && docker buildx build \
		-f $(COMPONENT)/Dockerfile \
		--target development \
		-t $(COMPONENT):development \
		--add-host host.docker.internal:host-gateway \
		--load \
		.
	@echo "[SUCCESS] Built $(COMPONENT):development"

build-prod:
	@echo "[BUILD] Building $(COMPONENT):production with BuildKit..."
	@echo "[INFO] Using PyPI Registry at http://localhost:9001/simple/"
	cd $(PROJECT_ROOT) && docker buildx build \
		-f $(COMPONENT)/Dockerfile \
		--target production \
		-t $(COMPONENT):production \
		--add-host host.docker.internal:host-gateway \
		--load \
		.
	docker tag $(COMPONENT):production $(COMPONENT):latest
	@echo "[SUCCESS] Built $(COMPONENT):production"

run-dev:
	@echo "[RUN] Starting $(COMPONENT):development on port $(PORT_DEV)..."
	docker run --rm -p $(PORT_DEV):$(PORT_DEV) \
		--env-file .env.development \
		--add-host host.docker.internal:host-gateway \
		--name $(COMPONENT)-dev \
		$(COMPONENT):development

run-prod:
	@echo "[RUN] Starting $(COMPONENT):production on port $(PORT_PROD)..."
	docker run --rm -p $(PORT_PROD):$(PORT_PROD) \
		--env-file .env.production \
		--add-host host.docker.internal:host-gateway \
		--name $(COMPONENT)-prod \
		$(COMPONENT):production

clean:
	@echo "[CLEAN] Removing $(COMPONENT) images..."
	docker rmi $(COMPONENT):development $(COMPONENT):production $(COMPONENT):latest 2>/dev/null || true
	@echo "[SUCCESS] Cleaned"

# Passeur Component Makefile

.PHONY: help build-dev build-prod run-dev run-prod clean

COMPONENT = passeur
PORT_DEV = 9766
PORT_PROD = 8766
PROJECT_ROOT = ..

help:
	@echo "=== Passeur Docker Commands ==="
	@echo "make build-dev   - Build development image"
	@echo "make build-prod  - Build production image"
	@echo "make run-dev     - Run development container"
	@echo "make run-prod    - Run production container"
	@echo "make clean       - Remove images"

build-dev:
	@echo "[BUILD] Building $(COMPONENT):development with BuildKit..."
	cd $(PROJECT_ROOT) && docker buildx build \
		-f $(COMPONENT)/Dockerfile \
		--target development \
		-t $(COMPONENT):development \
		--load \
		.
	@echo "[SUCCESS] Built $(COMPONENT):development"

build-prod:
	@echo "[BUILD] Building $(COMPONENT):production with BuildKit..."
	cd $(PROJECT_ROOT) && docker buildx build \
		-f $(COMPONENT)/Dockerfile \
		--target production \
		-t $(COMPONENT):production \
		--load \
		.
	docker tag $(COMPONENT):production $(COMPONENT):latest
	@echo "[SUCCESS] Built $(COMPONENT):production"

run-dev:
	@echo "[RUN] Starting $(COMPONENT):development on port $(PORT_DEV)..."
	docker run --rm -p $(PORT_DEV):$(PORT_DEV) \
		--env-file .env.development \
		--name $(COMPONENT)-dev \
		$(COMPONENT):development

run-prod:
	@echo "[RUN] Starting $(COMPONENT):production on port $(PORT_PROD)..."
	docker run --rm -p $(PORT_PROD):$(PORT_PROD) \
		--env-file .env.production \
		--name $(COMPONENT)-prod \
		$(COMPONENT):production

clean:
	@echo "[CLEAN] Removing $(COMPONENT) images..."
	docker rmi $(COMPONENT):development $(COMPONENT):production $(COMPONENT):latest 2>/dev/null || true
	@echo "[SUCCESS] Cleaned"

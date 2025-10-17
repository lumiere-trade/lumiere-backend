# Passeur Component Makefile

.PHONY: help build-dev build-prod run-dev run-prod clean

COMPONENT = passeur
PORT = 8766
KEYPAIRS_DIR = $(HOME)/lumiere/keypairs

help:
	@echo "=== Passeur Docker Commands ==="
	@echo "make build-dev   - Build development image"
	@echo "make build-prod  - Build production image"
	@echo "make run-dev     - Run development container"
	@echo "make run-prod    - Run production container"
	@echo "make clean       - Remove images"

build-dev:
	@echo "[BUILD] Building $(COMPONENT):development with BuildKit..."
	docker buildx build --target development -t $(COMPONENT):development --load .
	@echo "[SUCCESS] Built $(COMPONENT):development"

build-prod:
	@echo "[BUILD] Building $(COMPONENT):production with BuildKit..."
	docker buildx build --target production -t $(COMPONENT):production --load .
	docker tag $(COMPONENT):production $(COMPONENT):latest
	@echo "[SUCCESS] Built $(COMPONENT):production"

run-dev:
	@echo "[RUN] Starting $(COMPONENT):development on port $(PORT)..."
	@echo "[INFO] Mounting keypairs from: $(KEYPAIRS_DIR)/dev"
	docker run --rm -p $(PORT):$(PORT) \
		--env-file .env.development \
		-v $(KEYPAIRS_DIR)/dev:/root/lumiere/keypairs/dev:ro \
		--name $(COMPONENT)-dev \
		$(COMPONENT):development

run-prod:
	@echo "[RUN] Starting $(COMPONENT):production on port $(PORT)..."
	@echo "[INFO] Mounting keypairs from: $(KEYPAIRS_DIR)/prod"
	docker run --rm -p $(PORT):$(PORT) \
		--env-file .env.production \
		-v $(KEYPAIRS_DIR)/prod:/root/lumiere/keypairs/prod:ro \
		--name $(COMPONENT)-prod \
		$(COMPONENT):production

clean:
	@echo "[CLEAN] Removing $(COMPONENT) images..."
	docker rmi $(COMPONENT):development $(COMPONENT):production $(COMPONENT):latest 2>/dev/null || true
	@echo "[SUCCESS] Cleaned"

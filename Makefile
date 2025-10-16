# Lumiere Project - Master Makefile
# Auto-discovers and manages all components with Makefiles

.PHONY: help list-components

# Find all directories with Makefiles (components)
COMPONENTS := $(dir $(wildcard */Makefile))
COMPONENTS := $(COMPONENTS:/=)

# Colors
GREEN = \033[0;32m
YELLOW = \033[0;33m
BLUE = \033[0;34m
NC = \033[0m

help:
	@echo "=================================="
	@echo "Lumiere Docker Management"
	@echo "=================================="
	@echo ""
	@echo "Usage: make <component>-<action>"
	@echo ""
	@echo "Actions:"
	@echo "  build-dev    - Build development image"
	@echo "  build-prod   - Build production image"
	@echo "  run-dev      - Run development container"
	@echo "  run-prod     - Run production container"
	@echo "  clean        - Remove images"
	@echo ""
	@echo "Bulk actions:"
	@echo "  make build-all-dev"
	@echo "  make build-all-prod"
	@echo "  make clean-all"
	@echo ""
	@echo "List components:"
	@echo "  make list-components"

# List discovered components
list-components:
	@echo "$(BLUE)[INFO]$(NC) Discovered components:"
	@for comp in $(COMPONENTS); do \
		echo "  - $$comp"; \
	done

# Generic rule: <component>-<action>
%-build-dev:
	@component=$*; \
	if [ -d "$$component" ] && [ -f "$$component/Makefile" ]; then \
		echo "$(GREEN)[$$component]$(NC) Building development..."; \
		cd $$component && $(MAKE) build-dev; \
	else \
		echo "$(YELLOW)[ERROR]$(NC) Component $$component not found or no Makefile"; \
		exit 1; \
	fi

%-build-prod:
	@component=$*; \
	if [ -d "$$component" ] && [ -f "$$component/Makefile" ]; then \
		echo "$(GREEN)[$$component]$(NC) Building production..."; \
		cd $$component && $(MAKE) build-prod; \
	else \
		echo "$(YELLOW)[ERROR]$(NC) Component $$component not found or no Makefile"; \
		exit 1; \
	fi

%-run-dev:
	@component=$*; \
	if [ -d "$$component" ] && [ -f "$$component/Makefile" ]; then \
		echo "$(GREEN)[$$component]$(NC) Running development..."; \
		cd $$component && $(MAKE) run-dev; \
	else \
		echo "$(YELLOW)[ERROR]$(NC) Component $$component not found or no Makefile"; \
		exit 1; \
	fi

%-run-prod:
	@component=$*; \
	if [ -d "$$component" ] && [ -f "$$component/Makefile" ]; then \
		echo "$(GREEN)[$$component]$(NC) Running production..."; \
		cd $$component && $(MAKE) run-prod; \
	else \
		echo "$(YELLOW)[ERROR]$(NC) Component $$component not found or no Makefile"; \
		exit 1; \
	fi

%-clean:
	@component=$*; \
	if [ -d "$$component" ] && [ -f "$$component/Makefile" ]; then \
		echo "$(YELLOW)[$$component]$(NC) Cleaning..."; \
		cd $$component && $(MAKE) clean; \
	else \
		echo "$(YELLOW)[ERROR]$(NC) Component $$component not found or no Makefile"; \
		exit 1; \
	fi

# Bulk commands - iterate over all discovered components
build-all-dev:
	@for comp in $(COMPONENTS); do \
		echo "$(GREEN)[$$comp]$(NC) Building development..."; \
		cd $$comp && $(MAKE) build-dev || exit 1; \
		cd ..; \
	done
	@echo "$(GREEN)[SUCCESS]$(NC) All development images built"

build-all-prod:
	@for comp in $(COMPONENTS); do \
		echo "$(GREEN)[$$comp]$(NC) Building production..."; \
		cd $$comp && $(MAKE) build-prod || exit 1; \
		cd ..; \
	done
	@echo "$(GREEN)[SUCCESS]$(NC) All production images built"

clean-all:
	@for comp in $(COMPONENTS); do \
		echo "$(YELLOW)[$$comp]$(NC) Cleaning..."; \
		cd $$comp && $(MAKE) clean || true; \
		cd ..; \
	done
	@echo "$(GREEN)[SUCCESS]$(NC) All images cleaned"

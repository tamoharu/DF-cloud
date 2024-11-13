# Comprehensive Makefile for Docker Management

# Variable definitions
PROJECT_NAME := inference-app
CONFIG_DIR := config
SETUP_DIR := setup
DOCKER_USERNAME := $(shell whoami)

# Load environment variables
ifneq (,$(wildcard $(CONFIG_DIR)/.env))
    include $(CONFIG_DIR)/.env
    export
endif

# Docker-related variables
DOCKER_IMAGE := gcr.io/$(PROJECT_ID)/$(PROJECT_NAME)
DOCKER_TAG := $(shell git describe --tags --always --dirty 2>/dev/null || echo "latest")
CONTAINER_NAME := $(PROJECT_NAME)-$(DOCKER_USERNAME)

# Colors for output
BLUE := \033[34m
GREEN := \033[32m
RED := \033[31m
YELLOW := \033[33m
NC := \033[0m # No Color

# Default target
.DEFAULT_GOAL := help

# Help message
.PHONY: help
help:
	@echo "$(BLUE)Docker Management Makefile$(NC)"
	@echo "$(GREEN)Basic Commands:$(NC)"
	@echo "  make setup         - Set up development environment"
	@echo "  make build        - Build Docker image"
	@echo "  make run         - Run container"
	@echo "  make stop        - Stop container"
	@echo "  make restart     - Restart container"
	@echo "$(GREEN)Development Commands:$(NC)"
	@echo "  make shell       - Start shell in container"
	@echo "  make logs        - Show container logs"
	@echo "  make status      - Show container status"
	@echo "$(GREEN)Management Commands:$(NC)"
	@echo "  make clean       - Remove unused containers and images"
	@echo "  make push        - Push image to GCR"
	@echo "  make pull        - Pull image from GCR"
	@echo "$(GREEN)Docker Compose Commands:$(NC)"
	@echo "  make compose-up  - Start services with Docker Compose"
	@echo "  make compose-down - Stop services with Docker Compose"
	@echo "$(GREEN)Other Commands:$(NC)"
	@echo "  make env         - Check environment variables"
	@echo "  make version     - Show version information"

# Development environment setup
.PHONY: setup
setup:
	@echo "$(BLUE)Setting up development environment...$(NC)"
	@if [ ! -f "$(CONFIG_DIR)/.env" ]; then \
		cp $(CONFIG_DIR)/.env.template $(CONFIG_DIR)/.env; \
		echo "$(YELLOW)Created $(CONFIG_DIR)/.env. Please edit as needed.$(NC)"; \
	fi
	@python3 install.py
	@echo "$(GREEN)Setup completed successfully$(NC)"

# Build Docker image
.PHONY: build
build:
	@echo "$(BLUE)Building Docker image: $(DOCKER_IMAGE):$(DOCKER_TAG)$(NC)"
	docker build -f $(SETUP_DIR)/Dockerfile \
		--build-arg BUILD_DATE=$(shell date -u +'%Y-%m-%dT%H:%M:%SZ') \
		--build-arg VCS_REF=$(shell git rev-parse --short HEAD) \
		--build-arg PROJECT_ID=$(PROJECT_ID) \
		-t $(DOCKER_IMAGE):$(DOCKER_TAG) \
		.

# Run container
.PHONY: run
run: check-env
	@echo "$(BLUE)Starting container...$(NC)"
	@docker ps -q -f name=$(CONTAINER_NAME) | grep -q . && \
		echo "$(YELLOW)Warning: Container is already running$(NC)" || \
		docker run --gpus all \
			--env-file $(CONFIG_DIR)/.env \
			--name $(CONTAINER_NAME) \
			-d $(DOCKER_IMAGE):$(DOCKER_TAG)
	@echo "$(GREEN)Container started successfully$(NC)"

# Stop container
.PHONY: stop
stop:
	@echo "$(BLUE)Stopping container...$(NC)"
	@docker stop $(CONTAINER_NAME) || echo "$(YELLOW)Container is not running$(NC)"

# Restart container
.PHONY: restart
restart: stop run

# Start shell in container
.PHONY: shell
shell:
	@echo "$(BLUE)Starting shell in container...$(NC)"
	@docker exec -it $(CONTAINER_NAME) /bin/bash || \
		echo "$(RED)Error: Container is not running$(NC)"

# Show logs
.PHONY: logs
logs:
	@docker logs -f $(CONTAINER_NAME) || \
		echo "$(RED)Error: Container not found$(NC)"

# Show container status
.PHONY: status
status:
	@echo "$(BLUE)Container Status:$(NC)"
	@docker ps -a --filter name=$(CONTAINER_NAME) --format \
		"ID: {{.ID}}\nName: {{.Names}}\nStatus: {{.Status}}\nPorts: {{.Ports}}"

# Cleanup
.PHONY: clean
clean: stop
	@echo "$(BLUE)Performing cleanup...$(NC)"
	@docker rm $(CONTAINER_NAME) 2>/dev/null || true
	@docker image prune -f
	@echo "$(GREEN)Cleanup completed$(NC)"

# Push to GCR
.PHONY: push
push: build
	@echo "$(BLUE)Pushing image to GCR...$(NC)"
	@docker push $(DOCKER_IMAGE):$(DOCKER_TAG)

# Pull from GCR
.PHONY: pull
pull:
	@echo "$(BLUE)Pulling image from GCR...$(NC)"
	@docker pull $(DOCKER_IMAGE):$(DOCKER_TAG)

# Docker Compose
.PHONY: compose-up
compose-up:
	@echo "$(BLUE)Starting services with Docker Compose...$(NC)"
	@docker-compose -f $(SETUP_DIR)/docker-compose.yml up -d --build

.PHONY: compose-down
compose-down:
	@echo "$(BLUE)Stopping services with Docker Compose...$(NC)"
	@docker-compose -f $(SETUP_DIR)/docker-compose.yml down

# Check environment variables
.PHONY: check-env
check-env:
	@if [ ! -f "$(CONFIG_DIR)/.env" ]; then \
		echo "$(RED)Error: $(CONFIG_DIR)/.env not found$(NC)"; \
		echo "$(YELLOW)Please run 'make setup' first$(NC)"; \
		exit 1; \
	fi

# Show environment variables
.PHONY: env
env: check-env
	@echo "$(BLUE)Current Environment Variables:$(NC)"
	@echo "PROJECT_ID: $(PROJECT_ID)"
	@echo "DOCKER_IMAGE: $(DOCKER_IMAGE)"
	@echo "DOCKER_TAG: $(DOCKER_TAG)"
	@echo "CONTAINER_NAME: $(CONTAINER_NAME)"

# Show version information
.PHONY: version
version:
	@echo "$(BLUE)Version Information:$(NC)"
	@echo "Docker: $(shell docker --version)"
	@echo "Docker Compose: $(shell docker-compose --version)"
	@echo "Image Tag: $(DOCKER_TAG)"
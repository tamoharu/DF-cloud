# Basic configuration
PROJECT_ID := df-backend
PROJECT_NAME := inference
CONFIG_DIR := config
SETUP_DIR := setup
DOCKER_USERNAME := $(shell whoami)

# Default GCP credentials path
GOOGLE_APPLICATION_CREDENTIALS ?= ${HOME}/.config/gcloud/application_default_credentials.json

# Docker configuration
DOCKER_IMAGE := gcr.io/$(PROJECT_ID)/$(PROJECT_NAME)
DOCKER_TAG := $(shell git describe --tags --always --dirty 2>/dev/null || echo "latest")
CONTAINER_NAME := $(PROJECT_NAME)-$(DOCKER_USERNAME)

# GPU detection and configuration
NVIDIA_SMI := $(shell command -v nvidia-smi 2> /dev/null)
NVIDIA_DOCKER := $(shell docker info 2>/dev/null | grep -i nvidia)
GPU_AVAILABLE := $(if $(and $(NVIDIA_SMI),$(NVIDIA_DOCKER)),true,false)
GPU_FLAGS := $(if $(filter true,$(GPU_AVAILABLE)),--gpus all,)
DEVICE_TYPE := $(if $(filter true,$(GPU_AVAILABLE)),gpu,cpu)

# Video processing parameters
VIDEO_PATH ?=

# Colors for output
BLUE := \033[34m
GREEN := \033[32m
RED := \033[31m
YELLOW := \033[33m
NC := \033[0m

# Default target
.DEFAULT_GOAL := help

# Help message
.PHONY: help
help:
	@echo "$(BLUE)Usage: make [target]$(NC)"
	@echo ""
	@echo "$(BLUE)Available targets:$(NC)"
	@echo "  $(BLUE)build$(NC)            Build Docker image"
	@echo "  $(BLUE)build-dev$(NC)        Build development environment"
	@echo "  $(BLUE)run-video$(NC)        Process video"
	@echo "  $(BLUE)setup-gcp-auth$(NC)   Setup GCP authentication"
	@echo "  $(BLUE)push$(NC)             Push image to GCR"
	@echo "  $(BLUE)pull$(NC)             Pull image from GCR"
	@echo "  $(BLUE)status$(NC)           Show current configuration"
	@echo "  $(BLUE)clean$(NC)            Clean up Docker resources"


# Build Docker image
.PHONY: build
build:
	@echo "$(BLUE)Building Docker image ($(DEVICE_TYPE) version)...$(NC)"
	docker build \
		--build-arg DEVICE_TYPE=$(DEVICE_TYPE) \
		--build-arg BUILD_DATE=$(shell date -u +'%Y-%m-%dT%H:%M:%SZ') \
		--build-arg VCS_REF=$(shell git rev-parse --short HEAD) \
		-t $(DOCKER_IMAGE):$(DOCKER_TAG) \
		-f $(SETUP_DIR)/Dockerfile \
		.

# Build development environment
.PHONY: build-dev
build-dev:
	@echo "$(BLUE)Building development environment...$(NC)"
	python setup/build-dev.py

# Validate video path
.PHONY: validate-video-path
validate-video-path:
	@if [ -z "$(VIDEO_PATH)" ]; then \
		echo "$(RED)Error: VIDEO_PATH is required$(NC)"; \
		echo "Usage: make run-video VIDEO_PATH=path/to/video"; \
		exit 1; \
	fi

# Validate GCP authentication
.PHONY: validate-gcp-auth
validate-gcp-auth:
	@if [ ! -f "$(GOOGLE_APPLICATION_CREDENTIALS)" ]; then \
		echo "$(RED)Error: GCP credentials not found at $(GOOGLE_APPLICATION_CREDENTIALS)$(NC)"; \
		echo "$(YELLOW)Please run: make setup-gcp-auth$(NC)"; \
		exit 1; \
	fi

# Process video
.PHONY: run-video
run-video: validate-video-path validate-gcp-auth
	@echo "$(BLUE)Processing video: $(VIDEO_PATH)$(NC)"
	@docker run $(GPU_FLAGS) \
		--rm \
		--env INFERENCE_ARGS="--video_path $(VIDEO_PATH)"\
		--env GOOGLE_APPLICATION_CREDENTIALS=/gcp/credentials.json \
		-v $(GOOGLE_APPLICATION_CREDENTIALS):/gcp/credentials.json:ro \
		-v $(shell pwd)/$(VIDEO_PATH):/app/$(VIDEO_PATH) \
		$(DOCKER_IMAGE):$(DOCKER_TAG)
	@echo "$(GREEN)Video processing completed.$(NC)"

# Setup GCP authentication
.PHONY: setup-gcp-auth
setup-gcp-auth:
	@echo "$(BLUE)Setting up GCP authentication...$(NC)"
	@gcloud auth application-default login
	@echo "$(GREEN)GCP authentication completed. Credentials saved at: $(GOOGLE_APPLICATION_CREDENTIALS)$(NC)"

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

# Show status
.PHONY: status
status:
	@echo "$(BLUE)Current Configuration:$(NC)"
	@echo "Device Type: $(DEVICE_TYPE)"
	@echo "Docker Image: $(DOCKER_IMAGE):$(DOCKER_TAG)"
	@if [ "$(DEVICE_TYPE)" = "gpu" ]; then \
		echo "$(GREEN)GPU Information:$(NC)"; \
		nvidia-smi --format=csv --query-gpu=gpu_name,memory.total,memory.free; \
	fi

# Clean up Docker resources
.PHONY: clean
clean:
	@echo "$(BLUE)Cleaning up Docker resources...$(NC)"
	@echo "Stopping and removing containers..."
	@docker ps -a --filter name=$(PROJECT_NAME) -q | xargs -r docker rm -f
	@echo "Removing dangling images..."
	@docker images -qf "dangling=true" | xargs -r docker rmi
	@echo "Removing project images..."
	@docker images $(DOCKER_IMAGE) -q | xargs -r docker rmi -f
	@echo "Pruning unused networks..."
	@docker network prune -f
	@echo "$(GREEN)Docker cleanup completed$(NC)"
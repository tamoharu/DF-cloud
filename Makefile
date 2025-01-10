PROJECT_ID := df-backend
PROJECT_NAME := inference
CONFIG_DIR := config
SETUP_DIR := setup
DOCKER_USERNAME := $(shell whoami)

GOOGLE_APPLICATION_CREDENTIALS ?= ${HOME}/.config/gcloud/application_default_credentials.json

DOCKER_IMAGE := gcr.io/$(PROJECT_ID)/$(PROJECT_NAME)
DOCKER_TAG := $(shell git describe --tags --always --dirty 2>/dev/null || echo "latest")
CONTAINER_NAME := $(PROJECT_NAME)-$(DOCKER_USERNAME)

NVIDIA_SMI := $(shell command -v nvidia-smi 2> /dev/null)
NVIDIA_DOCKER := $(shell docker info 2>/dev/null | grep -i nvidia)
GPU_AVAILABLE := $(if $(and $(NVIDIA_SMI),$(NVIDIA_DOCKER)),true,false)
GPU_FLAGS := $(if $(filter true,$(GPU_AVAILABLE)),--gpus all,)
DEVICE_TYPE := $(if $(filter true,$(GPU_AVAILABLE)),gpu,cpu)

VIDEO_PATH ?=
VIDEO_DIR ?=
USER_DIR ?=

BLUE := \033[34m
GREEN := \033[32m
RED := \033[31m
YELLOW := \033[33m
NC := \033[0m

.DEFAULT_GOAL := help


.PHONY: help
help:
	@echo "$(BLUE)Usage: make [target]$(NC)"
	@echo ""
	@echo "$(BLUE)Available targets:$(NC)"
	@echo "  $(BLUE)build$(NC)            Build Docker image"
	@echo "  $(BLUE)build-dev$(NC)        Build development environment"
	@echo "  $(BLUE)run-video$(NC)        Process video"
	@echo "  $(BLUE)push$(NC)             Push image to GCR"
	@echo "  $(BLUE)pull$(NC)             Pull image from GCR"
	@echo "  $(BLUE)status$(NC)           Show current configuration"
	@echo "  $(BLUE)clean$(NC)            Clean up Docker resources"


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


.PHONY: build-dev
build-dev:
	@echo "$(BLUE)Building development environment...$(NC)"
	sudo sudo apt install python3-venv
	python3 setup/build-dev.py


.PHONY: validate-gcp-auth
validate-gcp-auth:
	@if [ ! -f "$(GOOGLE_APPLICATION_CREDENTIALS)" ]; then \
		echo "$(YELLOW)GCP credentials not found. Starting authentication setup...$(NC)"; \
		gcloud auth application-default login && \
		echo "$(GREEN)GCP authentication completed. Credentials saved at: $(GOOGLE_APPLICATION_CREDENTIALS)$(NC)"; \
	else \
		echo "$(GREEN)GCP credentials found at: $(GOOGLE_APPLICATION_CREDENTIALS)$(NC)"; \
	fi


.PHONY: validate-video-args
validate-video-args:
	@if [ -z "$(VIDEO_PATH)" ]; then \
		echo "$(RED)Error: VIDEO_PATH is required$(NC)"; \
		echo "Usage: make run-video VIDEO_PATH=path/to/video"; \
		exit 1; \
	fi


.PHONY: validate-swap-args
validate-swap-args:
	@if [ -z "$(VIDEO_DIR)" ]; then \
		echo "$(RED)Error: VIDEO_DIR is required$(NC)"; \
		echo "Usage: make run-swap VIDEO_DIR=path/to/video"; \
		exit 1; \
	fi
	@if [ -z "$(USER_DIR)" ]; then \
		echo "$(RED)Error: USER_DIR is required$(NC)"; \
		echo "Usage: make run-swap USER_DIR=path/to/user"; \
		exit 1; \
	fi


.PHONY: run-video
run-video: validate-video-args validate-gcp-auth
	@echo "$(BLUE)Processing video: $(VIDEO_PATH)$(NC)"
	@docker run $(GPU_FLAGS) \
		--rm \
		--env PROCESS_MODE=video \
		--env INFERENCE_ARGS="--video_path $(VIDEO_PATH)" \
		--env GOOGLE_APPLICATION_CREDENTIALS=/gcp/credentials.json \
		-v $(GOOGLE_APPLICATION_CREDENTIALS):/gcp/credentials.json:ro \
		-v $(shell pwd)/$(VIDEO_PATH):/app/$(VIDEO_PATH) \
		$(DOCKER_IMAGE):$(DOCKER_TAG)
	@echo "$(GREEN)Video processing completed.$(NC)"


.PHONY: run-swap
run-swap: validate-swap-args validate-gcp-auth
	@echo "$(BLUE)Processing video: $(VIDEO_DIR)$(NC)"
	@docker run $(GPU_FLAGS) \
		--rm \
		--env PROCESS_MODE=swap \
		--env INFERENCE_ARGS="--video_dir $(VIDEO_DIR) --user_dir $(USER_DIR)" \
		--env GOOGLE_APPLICATION_CREDENTIALS=/gcp/credentials.json \
		-v $(GOOGLE_APPLICATION_CREDENTIALS):/gcp/credentials.json:ro \
		-v $(shell pwd)/$(VIDEO_DIR):/app/$(VIDEO_DIR) \
		-v $(shell pwd)/$(USER_DIR):/app/$(USER_DIR) \
		$(DOCKER_IMAGE):$(DOCKER_TAG)
	@echo "$(GREEN)Swap processing completed.$(NC)"


.PHONY: push
push: build
	@echo "$(BLUE)Pushing image to GCR...$(NC)"
	@docker push $(DOCKER_IMAGE):$(DOCKER_TAG)


.PHONY: pull
pull:
	@echo "$(BLUE)Pulling image from GCR...$(NC)"
	@docker pull $(DOCKER_IMAGE):$(DOCKER_TAG)


.PHONY: status
status:
	@echo "$(BLUE)Current Configuration:$(NC)"
	@echo "Device Type: $(DEVICE_TYPE)"
	@echo "Docker Image: $(DOCKER_IMAGE):$(DOCKER_TAG)"
	@if [ "$(DEVICE_TYPE)" = "gpu" ]; then \
		echo "$(GREEN)GPU Information:$(NC)"; \
		nvidia-smi --format=csv --query-gpu=gpu_name,memory.total,memory.free; \
	fi


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

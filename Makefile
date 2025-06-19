# Satellite MCP Server - Simple Build Automation

.PHONY: help install run clean docker-build docker-run health-check

# Default target
help: ## Show available commands
	@echo "Satellite MCP Server"
	@echo "==================="
	@echo ""
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

# Variables
PYTHON := python3
PIP := pip3
DOCKER := docker

PROJECT_NAME := satellite-mcp-server
IMAGE_NAME := $(PROJECT_NAME)
SRC_DIR := src

# Installation
install: ## Install required dependencies
	$(PIP) install -r requirements.txt

# Execution
run: ## Run the MCP server
	$(PYTHON) -m $(SRC_DIR).mcp_server

# Docker
docker-build: ## Build Docker image
	$(DOCKER) build -t $(IMAGE_NAME):latest .

docker-run: ## Run Docker container
	$(DOCKER) run -it --rm --name $(PROJECT_NAME) $(IMAGE_NAME):latest

docker-stop: ## Stop Docker container
	$(DOCKER) stop $(PROJECT_NAME) || true

# Utilities
clean: ## Clean temporary files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf .mypy_cache

health-check: ## Check system dependencies
	@echo "Checking Python version..."
	$(PYTHON) --version
	@echo "Checking core dependencies..."
	$(PYTHON) -c "import skyfield, numpy; print('✓ Core dependencies OK')"
	@echo "Checking MCP server..."
	$(PYTHON) -c "from $(SRC_DIR).satellite_calc import SatelliteCalculator; print('✓ Satellite calculator OK')"
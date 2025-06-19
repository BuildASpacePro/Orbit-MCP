# Satellite MCP Server Makefile
# Build automation for satellite orbital mechanics MCP server

.PHONY: help install install-dev test test-verbose test-coverage lint format type-check \
        build run clean docker-build docker-run docker-stop docker-clean \
        docs serve-docs validate benchmark

# Default target
help: ## Show this help message
	@echo "Satellite MCP Server - Build Automation"
	@echo "======================================"
	@echo ""
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Variables
PYTHON := python3
PIP := pip3
PYTEST := pytest
BLACK := black
FLAKE8 := flake8
MYPY := mypy
DOCKER := docker
DOCKER_COMPOSE := docker-compose

PROJECT_NAME := satellite-mcp-server
IMAGE_NAME := $(PROJECT_NAME)
CONTAINER_NAME := $(PROJECT_NAME)

SRC_DIR := src
TEST_DIR := tests
DOCS_DIR := docs

# Python environment
VENV_DIR := venv
VENV_ACTIVATE := $(VENV_DIR)/bin/activate
PYTHON_VENV := $(VENV_DIR)/bin/python
PIP_VENV := $(VENV_DIR)/bin/pip

# Installation targets
install: ## Install production dependencies
	$(PIP) install -r requirements.txt

install-dev: ## Install development dependencies
	$(PIP) install -r requirements.txt -r requirements-dev.txt

venv: ## Create virtual environment
	$(PYTHON) -m venv $(VENV_DIR)
	$(PIP_VENV) install --upgrade pip setuptools wheel

venv-install: venv ## Create virtual environment and install dependencies
	$(PIP_VENV) install -r requirements.txt -r requirements-dev.txt

# Testing targets
test: ## Run all tests
	$(PYTEST) $(TEST_DIR) -v

test-verbose: ## Run tests with verbose output
	$(PYTEST) $(TEST_DIR) -v -s

test-coverage: ## Run tests with coverage report
	$(PYTEST) $(TEST_DIR) --cov=$(SRC_DIR) --cov-report=html --cov-report=term-missing

test-unit: ## Run unit tests only
	$(PYTEST) $(TEST_DIR)/test_calculations.py -v

test-integration: ## Run integration tests only
	$(PYTEST) $(TEST_DIR)/test_mcp_server.py -v

test-watch: ## Run tests in watch mode
	$(PYTEST) $(TEST_DIR) -v --tb=short -f

# Code quality targets
lint: ## Run linting checks
	$(FLAKE8) $(SRC_DIR) $(TEST_DIR) --max-line-length=100 --ignore=E203,W503

format: ## Format code with black
	$(BLACK) $(SRC_DIR) $(TEST_DIR) --line-length=100

format-check: ## Check code formatting
	$(BLACK) $(SRC_DIR) $(TEST_DIR) --line-length=100 --check

type-check: ## Run type checking with mypy
	$(MYPY) $(SRC_DIR) --ignore-missing-imports

quality: lint type-check format-check ## Run all code quality checks

# Docker targets
docker-build: ## Build Docker image
	$(DOCKER) build -f Dockerfile -t $(IMAGE_NAME):latest .

docker-build-dev: ## Build Docker image for development
	$(DOCKER) build -f Dockerfile -t $(IMAGE_NAME):dev --target builder .

docker-run: ## Run Docker container
	$(DOCKER) run -it --rm --name $(CONTAINER_NAME) $(IMAGE_NAME):latest

docker-run-background: ## Run Docker container in background
	$(DOCKER) run -d --name $(CONTAINER_NAME) $(IMAGE_NAME):latest

docker-stop: ## Stop Docker container
	$(DOCKER) stop $(CONTAINER_NAME) || true

docker-clean: ## Remove Docker container and image
	$(DOCKER) rm $(CONTAINER_NAME) || true
	$(DOCKER) rmi $(IMAGE_NAME):latest || true
	$(DOCKER) rmi $(IMAGE_NAME):dev || true

docker-compose-up: ## Start services with docker-compose
	$(DOCKER_COMPOSE) up -d

docker-compose-down: ## Stop services with docker-compose
	$(DOCKER_COMPOSE) down

docker-compose-logs: ## View docker-compose logs
	$(DOCKER_COMPOSE) logs -f

# Development targets
run: ## Run MCP server locally
	$(PYTHON) -m $(SRC_DIR).mcp_server_standalone

run-dev: ## Run MCP server in development mode with logging
	MCP_SERVER_LOG_LEVEL=DEBUG $(PYTHON) -m $(SRC_DIR).mcp_server_standalone

debug: ## Run with Python debugger
	$(PYTHON) -m pdb -m $(SRC_DIR).mcp_server_standalone

# Validation and benchmarking
validate: ## Validate TLE data and calculations
	$(PYTHON) -c "from $(SRC_DIR).satellite_calc import SatelliteCalculator; \
	from tests.sample_data import ISS_TLE; \
	calc = SatelliteCalculator(); \
	result = calc.validate_tle(ISS_TLE['line1'], ISS_TLE['line2']); \
	print('TLE Validation:', 'PASSED' if result.is_valid else 'FAILED')"

benchmark: ## Run performance benchmarks
	$(PYTHON) -c "import time; \
	from datetime import datetime, timezone, timedelta; \
	from $(SRC_DIR).satellite_calc import SatelliteCalculator; \
	from tests.sample_data import ISS_TLE, GROUND_STATIONS; \
	calc = SatelliteCalculator(); \
	start = datetime(2024, 1, 1, tzinfo=timezone.utc); \
	end = start + timedelta(days=1); \
	station = GROUND_STATIONS['MIT']; \
	start_time = time.time(); \
	windows = calc.calculate_access_windows(station['latitude'], station['longitude'], ISS_TLE['line1'], ISS_TLE['line2'], start, end); \
	end_time = time.time(); \
	print(f'Benchmark: {len(windows)} access windows calculated in {end_time-start_time:.2f} seconds')"

# Documentation targets
docs: ## Build documentation
	@echo "Building documentation..."
	@mkdir -p $(DOCS_DIR)
	@echo "Documentation structure created in $(DOCS_DIR)/"

serve-docs: ## Serve documentation locally
	@echo "Documentation would be served at http://localhost:8000"
	@echo "Run 'make docs' first to build documentation"

# Cleanup targets
clean: ## Clean temporary files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf .mypy_cache
	rm -rf build
	rm -rf dist
	rm -rf *.egg-info

clean-all: clean docker-clean ## Clean everything including Docker artifacts
	rm -rf $(VENV_DIR)

# Build targets
build: quality test ## Build and validate the project
	@echo "Build completed successfully!"

release: build ## Prepare for release
	@echo "Project ready for release"
	@echo "Docker image: $(IMAGE_NAME):latest"
	@echo "Run 'make docker-build' to build container"

# CI/CD targets
ci: install-dev quality test ## Run CI pipeline
	@echo "CI pipeline completed successfully"

cd: ci docker-build ## Run CD pipeline
	@echo "CD pipeline completed successfully"
	@echo "Docker image built: $(IMAGE_NAME):latest"

# Health check
health-check: ## Check system health and dependencies
	@echo "Checking Python version..."
	$(PYTHON) --version
	@echo "Checking pip version..."
	$(PIP) --version
	@echo "Checking Docker version..."
	$(DOCKER) --version || echo "Docker not available"
	@echo "Checking dependencies..."
	$(PYTHON) -c "import skyfield, numpy; print('Core dependencies OK')"

# Example usage
example: ## Run example calculation
	$(PYTHON) -c "from $(SRC_DIR).satellite_calc import SatelliteCalculator; \
	from tests.sample_data import ISS_TLE, GROUND_STATIONS, TEST_TIME_WINDOWS; \
	calc = SatelliteCalculator(); \
	windows = calc.calculate_access_windows( \
		GROUND_STATIONS['MIT']['latitude'], \
		GROUND_STATIONS['MIT']['longitude'], \
		ISS_TLE['line1'], ISS_TLE['line2'], \
		TEST_TIME_WINDOWS['SINGLE_DAY']['start'], \
		TEST_TIME_WINDOWS['SINGLE_DAY']['end']); \
	print(f'Example: Found {len(windows)} ISS passes over MIT today')"

# Default development workflow
dev: venv-install quality test ## Set up development environment and run checks
	@echo "Development environment ready!"
	@echo "Activate virtual environment: source $(VENV_ACTIVATE)"
	@echo "Run server: make run-dev"
.PHONY: install run test build lint format test-all test-ci clean help

# Default target
help:
	@echo "Available targets:"
	@echo "  install     - Install dependencies with Poetry"
	@echo "  run         - Run the DoIP server"
	@echo "  test        - Run all tests"
	@echo "  test-unit   - Run unit tests only"
	@echo "  test-integration - Run integration tests only"
	@echo "  test-hierarchical - Run hierarchical configuration tests"
	@echo "  test-cycling - Run response cycling tests"
	@echo "  test-all    - Run all test categories"
	@echo "  test-ci     - Run tests simulating CI environment"
	@echo "  test-python310 - Run tests with Python 3.10"
	@echo "  test-python311 - Run tests with Python 3.11"
	@echo "  test-python312 - Run tests with Python 3.12"
	@echo "  test-python313 - Run tests with Python 3.13"
	@echo "  lint        - Run flake8 linting"
	@echo "  format      - Format code with black"
	@echo "  format-check - Check code formatting without changes"
	@echo "  security    - Run security checks (bandit, safety)"
	@echo "  validate    - Validate configuration files"
	@echo "  demo        - Run demo scripts"
	@echo "  build       - Build package"
	@echo "  clean       - Clean build artifacts and cache"
	@echo "  ci-local    - Run full CI pipeline locally"

# Installation
install:
	poetry install

# Running the application
run:
	poetry run python src/doip_server/main.py

run-hierarchical:
	poetry run python src/doip_server/main.py --gateway-config config/gateway1.yaml


# Testing
test:
	poetry run pytest tests/ -v

test-unit:
	poetry run pytest tests/test_doip_unit.py -v

test-integration:
	poetry run pytest tests/test_doip_integration.py tests/test_doip_integration_updated.py -v

test-hierarchical:
	poetry run pytest tests/test_hierarchical_configuration.py -v

test-cycling:
	poetry run pytest tests/test_response_cycling.py -v

test-all:
	@echo "Running all test categories..."
	@$(MAKE) test-unit
	@$(MAKE) test-hierarchical
	@$(MAKE) test-cycling
	@$(MAKE) test-integration

# CI simulation
test-ci:
	@echo "Running CI simulation..."
	@$(MAKE) test-unit
	@$(MAKE) test-integration
	@$(MAKE) test-hierarchical
	@$(MAKE) test-cycling
	@$(MAKE) lint
	@$(MAKE) format-check
	@$(MAKE) security
	@$(MAKE) validate

# Multi-version testing
test-python310:
	@echo "Testing with Python 3.10..."
	@if command -v python3.10 >/dev/null 2>&1; then \
		python3.10 -m venv .venv-310 && \
		.venv-310/bin/pip install --upgrade pip && \
		.venv-310/bin/pip install -e . && \
		.venv-310/bin/pip install pytest pytest-cov flake8 black bandit safety && \
		.venv-310/bin/python -m pytest tests/ -v; \
	else \
		echo "Python 3.10 not found, skipping..."; \
	fi

test-python311:
	@echo "Testing with Python 3.11..."
	@if command -v python3.11 >/dev/null 2>&1; then \
		python3.11 -m venv .venv-311 && \
		.venv-311/bin/pip install --upgrade pip && \
		.venv-311/bin/pip install -e . && \
		.venv-311/bin/pip install pytest pytest-cov flake8 black bandit safety && \
		.venv-311/bin/python -m pytest tests/ -v; \
	else \
		echo "Python 3.11 not found, skipping..."; \
	fi

test-python312:
	@echo "Testing with Python 3.12..."
	@if command -v python3.12 >/dev/null 2>&1; then \
		python3.12 -m venv .venv-312 && \
		.venv-312/bin/pip install --upgrade pip && \
		.venv-312/bin/pip install -e . && \
		.venv-312/bin/pip install pytest pytest-cov flake8 black bandit safety && \
		.venv-312/bin/python -m pytest tests/ -v; \
	else \
		echo "Python 3.12 not found, skipping..."; \
	fi

test-python313:
	@echo "Testing with Python 3.13..."
	@if command -v python3.13 >/dev/null 2>&1; then \
		python3.13 -m venv .venv-313 && \
		.venv-313/bin/pip install --upgrade pip && \
		.venv-313/bin/pip install -e . && \
		.venv-313/bin/pip install pytest pytest-cov flake8 black bandit safety && \
		.venv-313/bin/python -m pytest tests/ -v; \
	else \
		echo "Python 3.13 not found, skipping..."; \
	fi

# Multi-version testing with Poetry
test-versions:
	@echo "Testing with multiple Python versions using Poetry..."
	@for version in 3.10 3.11 3.12 3.13; do \
		echo "Testing Python $$version..."; \
		poetry env use python$$version 2>/dev/null || echo "Python $$version not available"; \
		poetry install --no-interaction --no-root || echo "Installation failed for Python $$version"; \
		poetry run pytest tests/ -v || echo "Tests failed for Python $$version"; \
	done

# Linting and formatting
lint:
	@echo "Running flake8 linting..."
	poetry run flake8 src/ tests/ --count --select=E9,F63,F7,F82 --show-source --statistics
	poetry run flake8 src/ tests/ --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

format:
	@echo "Formatting code with black..."
	poetry run black src/ tests/

format-check:
	@echo "Checking code formatting..."
	poetry run black --check --diff src/ tests/

# Security checks
security:
	@echo "Running security checks..."
	poetry run bandit -r src/ -f json -o bandit-report.json || true
	poetry run safety check --json > safety-report.json || true
	@echo "Security reports generated: bandit-report.json, safety-report.json"

# Configuration validation
validate:
	@echo "Validating hierarchical configuration..."
	poetry run python -c "from src.doip_server.hierarchical_config_manager import HierarchicalConfigManager; HierarchicalConfigManager('config/gateway1.yaml')"

# Demo scripts
demo:
	@echo "Running demo scripts..."
	poetry run python test_udp_doip.py
	poetry run python test_functional_diagnostics.py

# Building
build:
	poetry build

# Full CI pipeline simulation
ci-local:
	@echo "Running full CI pipeline locally..."
	@echo "1. Installing dependencies..."
	@$(MAKE) install
	@echo "2. Running linting..."
	@$(MAKE) lint
	@echo "3. Checking formatting..."
	@$(MAKE) format-check
	@echo "4. Running security checks..."
	@$(MAKE) security
	@echo "5. Validating configurations..."
	@$(MAKE) validate
	@echo "6. Running all tests..."
	@$(MAKE) test-all
	@echo "7. Building package..."
	@$(MAKE) build
	@echo "CI pipeline completed successfully!"

# Cleanup
clean:
	@echo "Cleaning build artifacts and cache..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf coverage.xml
	rm -rf bandit-report.json
	rm -rf safety-report.json
	rm -rf .venv-*
	poetry env remove --all 2>/dev/null || true
	@echo "Cleanup completed!"
.PHONY: help validate validate-fast test test-cov check install

PYTHON := python3

help:
	@echo "Available commands:"
	@echo "  make validate      - Check for import errors and syntax issues (all src files)"
	@echo "  make validate-fast - Fast validation (syntax only, no import checking)"
	@echo "  make test          - Run all tests"
	@echo "  make test-cov      - Run tests with coverage report"
	@echo "  make check         - Run validation and tests (recommended before commit)"
	@echo "  make install       - Install development dependencies"

validate:
	@echo "Running validation..."
	@$(PYTHON) scripts/validate.py

validate-fast:
	@echo "Running fast validation (syntax only)..."
	@$(PYTHON) scripts/validate.py --no-import-check

test:
	@echo "Running tests..."
	@pytest

test-cov:
	@echo "Running tests with coverage..."
	@pytest --cov=src --cov-report=html --cov-report=term-missing

check: validate test
	@echo "✅ All checks passed!"

install:
	@echo "Installing development dependencies..."
	@pip install -e ".[dev]"


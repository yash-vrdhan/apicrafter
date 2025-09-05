# Makefile for apicrafter

.PHONY: help install install-dev test lint format clean build publish test-publish

# Default target
help:
	@echo "Available commands:"
	@echo "  install      Install the package in development mode"
	@echo "  install-dev  Install development dependencies"
	@echo "  test         Run tests"
	@echo "  lint         Run linting checks"
	@echo "  format       Format code with black and isort"
	@echo "  clean        Clean build artifacts"
	@echo "  build        Build the package"
	@echo "  publish      Publish to PyPI (interactive)"
	@echo "  test-publish Publish to TestPyPI only"
	@echo "  dry-run      Show what would be published without doing it"

# Install the package in development mode
install:
	pip install -e .

# Install development dependencies
install-dev:
	pip install -e ".[dev]"

# Run tests
test:
	pytest tests/ -v

# Run linting checks
lint:
	black apicrafter/ --check
	isort apicrafter/ --check-only
	mypy apicrafter/

# Format code
format:
	black apicrafter/
	isort apicrafter/

# Clean build artifacts
clean:
	rm -rf build/ dist/ *.egg-info/ .pytest_cache/ .coverage htmlcov/

# Build the package
build: clean
	python -m build

# Publish to PyPI (interactive)
publish: build
	./scripts/publish.sh

# Publish to TestPyPI only
test-publish: build
	./scripts/publish.sh --test-only

# Dry run (show what would be published)
dry-run: build
	./scripts/publish.sh --dry-run

# Quick development setup
setup: install-dev
	@echo "Development environment ready!"
	@echo "Run 'make test' to run tests"
	@echo "Run 'make format' to format code"
	@echo "Run 'make publish' to publish to PyPI"

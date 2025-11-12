.PHONY: run dev install install-dev format lint clean help

# Default target
.DEFAULT_GOAL := help

# Variables
APP_MODULE := run:app
HOST := 0.0.0.0
PORT := 8001  # Use different port to avoid conflicts

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies using uv
	uv sync

install-dev: ## Install dependencies with dev extras (if any)
	uv sync --dev

run: ## Run the FastAPI application
	uv run uvicorn $(APP_MODULE) --host $(HOST) --port $(PORT)

dev: ## Run the FastAPI application with auto-reload
	uv run uvicorn $(APP_MODULE) --host $(HOST) --port $(PORT) --reload

format: ## Format code with ruff (if installed) or black
	@if command -v ruff > /dev/null; then \
		uv run ruff format .; \
	else \
		echo "ruff not found, install it with: uv add --dev ruff"; \
	fi

lint: ## Lint code with ruff (if installed)
	@if command -v ruff > /dev/null; then \
		uv run ruff check .; \
	else \
		echo "ruff not found, install it with: uv add --dev ruff"; \
	fi

clean: ## Clean up temporary files and caches
	find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -r {} + 2>/dev/null || true
	rm -rf .pytest_cache .mypy_cache .ruff_cache

test: ## Run tests (if pytest is installed)
	@if command -v pytest > /dev/null; then \
		uv run pytest; \
	else \
		echo "pytest not found, install it with: uv add --dev pytest"; \
	fi

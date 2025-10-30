# Modern Python Project Commands
# Just like npm scripts, but even simpler: make <command>

.PHONY: dev start test lint format setup-github health

# Development
dev:
	env AWS_PROFILE=mingfang uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

start:
	env AWS_PROFILE=mingfang uv run uvicorn src.main:app --host 0.0.0.0 --port 8000

# Testing
test:
	uv run python -m pytest tests/ -v

test-cov:
	uv run python -m pytest tests/ --cov=src --cov-report=term-missing

# Code Quality
lint:
	uv run ruff check src/ tests/

format:
	uv run ruff format src/ tests/

# Setup
setup-github:
	uv run python -m src.auth.setup_provider

# Utilities
health:
	@curl -s http://localhost:8000/health | python -m json.tool

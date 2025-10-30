# Command Reference

Quick reference for all project commands using Makefile (like npm scripts).

## Development

```bash
# Start development server with hot reload
make dev

# Start production server
make start
```

## Testing

```bash
# Run all tests
make test

# Run tests with coverage report
make test-cov
```

## Code Quality

```bash
# Check code style and errors
make lint

# Auto-format code
make format
```

## Setup & Configuration

```bash
# Setup GitHub OAuth provider (one-time)
make setup-github
```

## Utilities

```bash
# Check if server is running
make health
```

## Examples

### Daily Development Workflow
```bash
# 1. Start server
make dev

# 2. In another terminal, run tests
make test

# 3. Check code quality before commit
make lint
```

### First-Time GitHub OAuth Setup
```bash
# 1. Create OAuth App at https://github.com/settings/developers
# 2. Add credentials to .env
# 3. Run setup
make setup-github
```

### Test Your Agent
```bash
# 1. Start server
make dev

# 2. In another terminal, test with curl
curl -X POST http://localhost:8000/chat/stream \
  -H 'Content-Type: application/json' \
  -d '{"message":"Write hello world in Python","session_id":"test"}' \
  --no-buffer
```

## Direct Commands (Alternative)

If you prefer explicit commands:

```bash
# Development server
env AWS_PROFILE=mingfang uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
uv run python -m pytest tests/ -v

# Setup GitHub OAuth
uv run python -m src.auth.setup_provider
```

## AWS Authentication

Make sure you're logged in to AWS SSO before starting:

```bash
aws sso login --profile mingfang
```

The Makefile automatically uses `AWS_PROFILE=mingfang` for all server commands.

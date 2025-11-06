# AWS Coding Agent - Makefile
# Modern Python Project Commands
#
# 💡 QUICK START:
#   1. make aws-login          # Login to AWS SSO (required first!)
#   2. make install            # Install dependencies
#   3. make dev                # Start development server
#
# 🚀 DEPLOYMENT:
#   First time:  make init-deploy    # Creates OAuth provider & IAM role
#   Updates:     make deploy         # Deploy code changes only
#
# 📚 HELP:
#   make help                  # Show all available commands

# ═══════════════════════════════════════════════════
# Configuration Variables
# ═══════════════════════════════════════════════════

# AWS Configuration (override via environment or command line)
# 💡 Tip: Set AWS_PROFILE=mingfang or your profile name
AWS_PROFILE ?= mingfang
AWS_REGION ?= ap-southeast-2
LOG_GROUP ?= /aws/bedrock/agentcore/coding-agent-production

# Server Configuration
HOST ?= 0.0.0.0
PORT ?= 8000

# Python Configuration
PYTHON := uv run python
UV := uv run

# ═══════════════════════════════════════════════════
# PHONY Targets
# ═══════════════════════════════════════════════════

.PHONY: help aws-login aws-check aws-status dev start test test-cov lint format setup-github
.PHONY: init-deploy deploy test-runtime logs health clean install login

# ═══════════════════════════════════════════════════
# Help
# ═══════════════════════════════════════════════════

help: ## Show this help message
	@echo "AWS Coding Agent - Available Commands"
	@echo ""
	@echo "💡 QUICK START:"
	@echo "  1. make aws-login    # Login to AWS SSO first!"
	@echo "  2. make install      # Install dependencies"
	@echo "  3. make dev          # Start development server"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "Configuration Variables:"
	@echo "  AWS_PROFILE=$(AWS_PROFILE)"
	@echo "  AWS_REGION=$(AWS_REGION)"
	@echo "  HOST=$(HOST)"
	@echo "  PORT=$(PORT)"

# ═══════════════════════════════════════════════════
# AWS Authentication
# ═══════════════════════════════════════════════════
# 💡 USAGE HINTS:
#   - Run 'make aws-login' before any AWS operation
#   - Use 'make aws-check' to verify credentials are valid
#   - SSO sessions expire after 12 hours by default

aws-login: ## Login to AWS SSO (required for Bedrock access)
	@echo "Logging in to AWS SSO..."
	@echo "Profile: $(AWS_PROFILE)"
	@echo "Region: $(AWS_REGION)"
	@aws sso login --profile $(AWS_PROFILE)
	@echo ""
	@echo "✓ AWS SSO login successful!"
	@echo "💡 Tip: Run 'make aws-status' to verify credentials"

aws-check: ## Check if AWS credentials are valid
	@echo "Checking AWS credentials..."
	@aws sts get-caller-identity --profile $(AWS_PROFILE) > /dev/null 2>&1 && \
		echo "✓ AWS credentials are valid" || \
		(echo "❌ AWS credentials expired or invalid" && echo "💡 Run: make aws-login" && exit 1)

aws-status: ## Show current AWS identity and session info
	@echo "AWS Identity Information:"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@aws sts get-caller-identity --profile $(AWS_PROFILE) --output table 2>/dev/null || \
		(echo "❌ Not logged in. Run: make aws-login" && exit 1)
	@echo ""
	@echo "Configuration:"
	@echo "  Profile: $(AWS_PROFILE)"
	@echo "  Region:  $(AWS_REGION)"

# ═══════════════════════════════════════════════════
# Development
# ═══════════════════════════════════════════════════
# 💡 USAGE HINTS:
#   - 'make dev' enables hot reload (auto-restarts on file changes)
#   - 'make start' runs production mode (no hot reload)
#   - Both require AWS credentials for Bedrock access

dev: aws-check ## Start development server with hot reload
	@echo "Starting development server on $(HOST):$(PORT)..."
	@echo "💡 Hot reload enabled - changes auto-restart server"
	env AWS_PROFILE=$(AWS_PROFILE) $(UV) uvicorn src.main:app --reload --host $(HOST) --port $(PORT)

start: aws-check ## Start production server
	@echo "Starting production server on $(HOST):$(PORT)..."
	env AWS_PROFILE=$(AWS_PROFILE) $(UV) uvicorn src.main:app --host $(HOST) --port $(PORT)

install: ## Install dependencies
	@echo "Installing dependencies..."
	uv pip install -e ".[dev]"

# ═══════════════════════════════════════════════════
# Testing
# ═══════════════════════════════════════════════════
# 💡 USAGE HINTS:
#   - 'make test' runs all tests with verbose output
#   - 'make test-cov' shows coverage report (aim for >80%)

test: ## Run tests
	@echo "Running tests..."
	@echo "💡 Use 'make test-cov' to see coverage report"
	$(UV) pytest tests/ -v

test-cov: ## Run tests with coverage report
	@echo "Running tests with coverage..."
	$(UV) pytest tests/ --cov=src --cov-report=term-missing

# ═══════════════════════════════════════════════════
# Code Quality
# ═══════════════════════════════════════════════════
# 💡 USAGE HINTS:
#   - 'make lint' checks code without modifying
#   - 'make format' auto-fixes formatting issues
#   - Run both before committing code

lint: ## Check code quality with ruff
	@echo "Checking code quality..."
	@echo "💡 Run 'make format' to auto-fix issues"
	$(UV) ruff check src/ tests/

format: ## Format code with ruff
	@echo "Formatting code..."
	$(UV) ruff format src/ tests/
	@echo "✓ Code formatted successfully"

# ═══════════════════════════════════════════════════
# Setup & Configuration
# ═══════════════════════════════════════════════════
# 💡 USAGE HINTS:
#   - Run 'make setup-github' to create OAuth provider in AWS
#   - Copy the callback URL from output
#   - Add callback URL to GitHub OAuth App settings

setup-github: aws-check ## Setup GitHub OAuth provider
	@echo "Setting up GitHub OAuth provider..."
	@echo "💡 You'll need to add the callback URL to your GitHub OAuth App"
	$(PYTHON) -m src.auth.setup_provider

# ═══════════════════════════════════════════════════
# Deployment
# ═══════════════════════════════════════════════════
# 💡 USAGE HINTS:
#   - First time: 'make init-deploy' creates OAuth provider & IAM role
#   - Updates: 'make deploy' deploys code changes only
#   - Both require valid AWS credentials (auto-checks before deploy)

init-deploy: aws-check ## First-time deployment (creates provider and role)
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "First-time deployment to AWS BedrockAgentCore"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo ""
	@echo "This will create:"
	@echo "  • GitHub OAuth provider"
	@echo "  • IAM execution role"
	@echo "  • Agent runtime"
	@echo ""
	@./scripts/deploy.sh

deploy: aws-check ## Deploy to AWS BedrockAgentCore (updates only)
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "Deploying to AWS BedrockAgentCore"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo ""
	@echo "Updating agent runtime (skipping provider/role creation)..."
	@./scripts/deploy.sh --skip-provider --skip-role

test-runtime: ## Test deployed runtime
	@echo "Testing deployed runtime..."
	@./scripts/test-runtime.sh

logs: aws-check ## Tail CloudWatch logs
	@echo "Tailing CloudWatch logs from $(LOG_GROUP)..."
	@echo "💡 Press Ctrl+C to stop"
	@echo ""
	aws logs tail $(LOG_GROUP) \
		--region $(AWS_REGION) \
		--follow \
		--format short \
		--profile $(AWS_PROFILE)

# ═══════════════════════════════════════════════════
# Utilities
# ═══════════════════════════════════════════════════
# 💡 USAGE HINTS:
#   - 'make health' checks if local server is running
#   - 'make clean' removes Python cache files
#   - 'make aws-status' shows current AWS identity

health: ## Check health endpoint
	@echo "Checking health endpoint..."
	@echo "💡 Make sure server is running (make dev)"
	@curl -s http://$(HOST):$(PORT)/health | $(PYTHON) -m json.tool || \
		echo "❌ Server not responding. Run 'make dev' first."

clean: ## Clean up temporary files and caches
	@echo "Cleaning up temporary files and caches..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@echo "✓ Cleanup complete"

# ═══════════════════════════════════════════════════
# Aliases (short commands for convenience)
# ═══════════════════════════════════════════════════

login: aws-login  ## Alias for aws-login

.DEFAULT_GOAL := help

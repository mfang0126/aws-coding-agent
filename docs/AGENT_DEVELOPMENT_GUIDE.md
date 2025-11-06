# Agent Development Guide

## Table of Contents

1. [Overview](#overview)
2. [Standard Folder Structure](#standard-folder-structure)
3. [File Purposes](#file-purposes)
4. [Dependencies & Tooling](#dependencies--tooling)
5. [Architecture Patterns](#architecture-patterns)
6. [Development Workflow](#development-workflow)
7. [Best Practices](#best-practices)
8. [AgentCore Integration](#agentcore-integration)

---

## Overview

This guide documents the standard patterns for building AWS Bedrock AgentCore agents using the Strands framework. It's based on analysis of production agents (github-agent, jira-agent) and establishes replicable patterns for modern Python development.

### Core Principles

- **Separation of Concerns**: Runtime deployment vs. agent logic vs. tools
- **Dependency Injection**: Protocol-based interfaces for flexibility
- **Modern Python**: Python 3.10+ with type hints, async/await, protocols
- **Hot Reload Support**: Local development with fast iteration cycles

---

## Standard Folder Structure

### Root Level Structure

```
agent-name/
├── .bedrock_agentcore.yaml    # AgentCore deployment configuration
├── .env.example                # Environment variables template
├── .gitignore                  # Standard Python gitignore
├── Dockerfile                  # Container build configuration
├── pyproject.toml             # Python project + dependencies
├── uv.lock                    # Locked dependencies (generated)
├── README.md                   # Agent-specific documentation
├── QUICKSTART.md              # Quick start guide (optional)
├── docs/                      # Extended documentation
├── scripts/                   # Setup and utility scripts
└── src/                       # Source code (main package)
```

### Source Code Structure (`src/`)

```
src/
├── __init__.py               # Clean imports (modern pattern)
├── runtime.py                # AgentCore deployment entrypoint
├── main.py                   # Pure Strands agent entrypoint (local testing)
├── agent.py                  # Agent factory (pure logic)
├── config.py                 # Runtime configuration (AWS, env vars)
├── constants/                # Static content (prompts, messages)
│   ├── __init__.py
│   ├── prompts.py           # System prompts, tool descriptions
│   └── messages.py          # Error messages, response templates
├── utils/                    # General utilities
│   ├── __init__.py
│   ├── response.py          # Response formatting & protocols
│   └── helpers.py           # General helper functions
├── gateway/                  # Auth implementations (flat structure)
│   ├── __init__.py
│   ├── interface.py         # Protocol definition (GatewayAuth)
│   ├── agentcore.py         # Generic AgentCore OAuth
│   ├── github.py            # GitHub-specific (example)
│   └── jira.py              # Jira-specific (example)
└── tools/                    # Agent tool implementations
    ├── __init__.py
    ├── resource_1.py        # Tool group 1 (e.g., repos)
    ├── resource_2.py        # Tool group 2 (e.g., issues)
    └── resource_3.py        # Tool group 3 (e.g., pull_requests)
```

### Documentation Structure (`docs/`)

```
docs/
├── OAuth-Testing-Guide.md          # OAuth setup instructions
├── Response-Format.md              # Response protocol documentation
├── Strands-Native-Orchestration.md # Framework patterns
└── exp-*.md                        # Experimental notes
```

### Scripts Structure (`scripts/`)

```
scripts/
├── setup_provider.sh        # OAuth provider setup
├── build_docker.sh          # Docker build helper
└── deploy.sh                # Deployment helper
```

---

## File Purposes

### Dual Entrypoint System

The agent has **two entrypoints** for different use cases:

#### `src/runtime.py` - AgentCore Deployment Entrypoint
**Purpose**: Production deployment and AgentCore integration testing

**Use cases:**
- Production deployment to AWS
- Testing with `agentcore launch --local` (validates AgentCore response format)
- OAuth streaming and callback handling
- Memory integration

**Responsibilities:**
- Create AgentCore app instance
- Configure Bedrock model
- Set up OAuth callbacks
- Handle streaming responses
- Wrap agent from `agent.py`

#### `src/main.py` - Pure Strands Entrypoint
**Purpose**: Local development and fast iteration

**Use cases:**
- Local testing without AgentCore overhead
- Direct Strands agent interaction
- Faster development cycle

**Responsibilities:**
- Pure Strands agent creation
- Command-line interface (optional)
- Local testing harness
- No AgentCore dependencies

**Pattern:**
```python
"""Pure Strands agent entrypoint for local testing."""

import asyncio
from src.agent import create_agent
from src.gateway import AgentCoreAuth

def main():
    """Run agent locally with OAuth from .env"""
    # Create auth (reads from .env)
    auth = AgentCoreAuth("provider-name")
    print("🔐 Using OAuth (configure in .env)")

    # Create agent
    agent = create_agent(auth)

    # Interactive loop
    print("Agent ready! Type your message (or 'quit' to exit)")
    while True:
        user_input = input("> ")
        if user_input.lower() in ["quit", "exit"]:
            break

        # Run agent
        response = asyncio.run(agent.run_async(user_input))
        print(f"\n{response}\n")

if __name__ == "__main__":
    main()
```

**Usage:**
```bash
# Configure .env first
cp .env.example .env
# Add your SERVICE_CLIENT_ID and SERVICE_CLIENT_SECRET

# Run locally
python -m src.main
python src/main.py
```

### Configuration Files

#### `pyproject.toml`

**Purpose**: Python project definition, dependencies, tooling configuration

**Structure**:

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "agent-name"
version = "0.1.0"
description = "Agent description"
requires-python = ">=3.10"  # or ">=3.12" for newer agents
dependencies = [
    "bedrock-agentcore[strands-agents]>=0.1.0",
    "bedrock-agentcore-starter-toolkit>=0.1.0",
    "strands-agents>=0.1.0",
    "httpx>=0.27.0",           # Async HTTP client
    "typer>=0.12.0",           # CLI framework
    "python-dotenv>=1.0.0",    # Environment variables
    "boto3>=1.39.15",          # AWS SDK
    "pydantic>=2.0.0",         # Data validation
    # Agent-specific dependencies here
]

[project.optional-dependencies]
dev = [
    "mypy>=1.0.0",
    "isort>=5.12.0",
    "black>=23.0.0",
]

[tool.hatch.build.targets.wheel]
packages = ["src"]

[project.scripts]
agent-name = "src.agent:main"

[tool.poe.tasks]
dev = "python -m src.runtime"
invoke = "agentcore invoke"
launch = "agentcore launch"

[tool.isort]
profile = "black"
multi_line_output = 3
line_length = 88
known_first_party = ["src"]

[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

**Key Sections**:

- `dependencies`: Core runtime dependencies
- `project.optional-dependencies`: Development-only tools
- `tool.poe.tasks`: Task runner commands for common operations
- `tool.isort` & `tool.mypy`: Code quality tools

#### `.bedrock_agentcore.yaml`

**Purpose**: AgentCore deployment configuration

**Structure**:

```yaml
default_agent: agent-name
agents:
  agent-name:
    name: agent-name
    entrypoint: src/runtime.py
    platform: linux/arm64
    container_runtime: docker
    aws:
      execution_role: arn:aws:iam::ACCOUNT:role/...
      account: 'ACCOUNT_ID'
      region: ap-southeast-2
      ecr_repository: ACCOUNT.dkr.ecr.REGION.amazonaws.com/repo
      network_configuration:
        network_mode: PUBLIC
    memory:
      mode: STM_ONLY
      memory_id: agent_mem-...
    oauth_configuration:
      workload_name: agent-name
      credential_providers:
        - provider-name
```

**Configuration Notes**:

- Auto-generated after first deployment
- Contains deployment state (IDs, ARNs)
- **Do not manually edit** AWS resource identifiers

#### `.env.example`

**Purpose**: Environment variables template for local development

**Structure**:

```bash
# Environment
AGENT_ENV=local  # local | dev | prod

# AWS Configuration
AWS_REGION=ap-southeast-2
AWS_PROFILE=your-profile

# Service OAuth Credentials
SERVICE_CLIENT_ID=your_client_id
SERVICE_CLIENT_SECRET=your_client_secret

# AgentCore (if needed)
AGENTCORE_AGENT_ID=
AGENTCORE_SESSION_ID=
```

**Usage**:

```bash
# Copy and configure for local development
cp .env.example .env
# Add your credentials to .env (gitignored)
```

#### `Dockerfile`

**Purpose**: Container image build configuration

**Standard Pattern**:

```dockerfile
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim
WORKDIR /app

# Environment variables for Python and AWS
ENV UV_SYSTEM_PYTHON=1 \
    UV_COMPILE_BYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    DOCKER_CONTAINER=1 \
    AWS_REGION=ap-southeast-2 \
    AWS_DEFAULT_REGION=ap-southeast-2

# Copy agent files (respecting .dockerignore)
COPY . .

# Install dependencies from pyproject.toml
RUN uv pip install .

# Create non-root user for security
RUN useradd -m -u 1000 bedrock_agentcore && \
    chown -R bedrock_agentcore:bedrock_agentcore /app

USER bedrock_agentcore

# Expose ports for AgentCore runtime
EXPOSE 9000 8000 8080

# Run the agent runtime
CMD ["python", "-m", "src.runtime"]
```

**Key Elements**:

- Uses `uv` for fast dependency installation
- Sets `PYTHONPATH=/app` for correct imports
- Non-root user for security
- Multi-port exposure for AgentCore services

---

### Source Code Files

#### `src/runtime.py`

**Purpose**: AgentCore deployment entrypoint (infrastructure layer)

**Responsibilities**:

- Create AgentCore app instance
- Configure Bedrock model
- Set up authentication callbacks
- Handle OAuth flow streaming
- Delegate to agent logic
- Format streaming responses

**Pattern**:

```python
"""Agent Runtime - AgentCore deployment entrypoint."""

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands import Agent
from strands.models import BedrockModel

# Import tools
from src.tools.resource1 import tool1, tool2
from src.tools.resource2 import tool3, tool4

# Create AgentCore app
app = BedrockAgentCoreApp()

# Model configuration
MODEL_ID = "anthropic.claude-3-5-sonnet-20241022-v2:0"
REGION = "ap-southeast-2"

model = BedrockModel(model_id=MODEL_ID, region_name=REGION)

# Create agent
agent = Agent(
    model=model,
    tools=[tool1, tool2, tool3, tool4],
    system_prompt="Agent instructions...",
)

@app.entrypoint
async def strands_agent_name(payload):
    """AgentCore Runtime entrypoint with streaming support."""
    from src.common import auth
    from src.common.utils import (
        AgentResponse,
        format_client_text,
        create_oauth_message,
    )

    user_input = payload.get("prompt", "")

    # OAuth callback setup
    oauth_url_queue = asyncio.Queue()

    def stream_oauth_url_callback(url: str):
        oauth_url_queue.put_nowait(url)

    auth.oauth_url_callback = stream_oauth_url_callback

    # Initialize authentication
    yield format_client_text("🔐 Initializing authentication...")

    # Handle OAuth or proceed with agent
    # ... (see github-agent/src/runtime.py for full pattern)

    # Stream agent responses
    async for event in agent.stream_async(user_input):
        extracted_text = extract_text_from_event(event)
        yield format_client_text(extracted_text)

if __name__ == "__main__":
    app.run()
```

**Key Pattern**:

- Infrastructure concerns only (OAuth, streaming, AgentCore)
- Delegates business logic to `agent.py`
- Handles deployment-specific configurations

#### `src/agent.py`

**Purpose**: Pure agent logic (testable, framework-agnostic)

**Responsibilities**:

- Agent factory function
- Tool assembly
- System prompt definition
- Dependency injection (auth)

**Pattern**:

```python
"""Agent - Pure agent logic without deployment concerns."""

from strands import Agent
from strands.models import BedrockModel

from src.auth import ServiceAuth
from src.tools.resource1 import resource1_tools
from src.tools.resource2 import resource2_tools

MODEL_ID = "anthropic.claude-3-5-sonnet-20241022-v2:0"
REGION = "ap-southeast-2"

def create_agent(auth: ServiceAuth) -> Agent:
    """Create agent with injected authentication.

    This factory function creates a fully configured agent using
    the provided authentication implementation.

    Args:
        auth: ServiceAuth implementation (OAuth via AgentCore)

    Returns:
        Agent: Configured Strands Agent with all tools

    Example:
        >>> from src.gateway import AgentCoreAuth
        >>> auth = AgentCoreAuth("provider-name")
        >>> agent = create_agent(auth)
        >>> response = agent("Test prompt")
    """
    model = BedrockModel(model_id=MODEL_ID, region_name=REGION)

    agent = Agent(
        model=model,
        tools=[
            *resource1_tools(auth),  # Tools with auth closure
            *resource2_tools(auth),  # Tools with auth closure
        ],
        system_prompt="""You are an assistant for [service].

        **Available Capabilities:**
        - Resource 1: list, create, update, delete
        - Resource 2: query, modify, analyze

        **Authentication:**
        Authentication is handled automatically. Never ask for credentials.

        **Best Practices:**
        - Confirm destructive actions
        - Provide clear feedback
        - Use markdown formatting
        - Include relevant URLs
        """,
    )

    return agent
```

**Architecture Benefits**:

- No AgentCore dependencies in agent logic
- No AWS dependencies in agent logic
- Pure function with dependency injection
- Flexible authentication via Protocol

#### `src/config.py`

**Purpose**: Runtime configuration management

**Location**: Root level of `src/` (not in subdirectory)

**Responsibilities**:
- Environment detection (local/dev/prod)
- Credential loading (env vars vs AWS Secrets Manager)
- AWS region configuration
- Service-specific settings

**Pattern**:
```python
"""Runtime configuration management."""

import json
import os
from typing import Dict
from dotenv import load_dotenv

def get_environment() -> str:
    """Get current environment from AGENT_ENV variable.

    Returns:
        str: "local", "dev", or "prod"
    """
    env = os.getenv("AGENT_ENV", "prod").lower()
    if env not in ["local", "dev", "prod"]:
        return "prod"
    return env

class Config:
    """Configuration manager."""

    def __init__(self, environment: str = "local"):
        self.environment = environment
        if environment == "local":
            load_dotenv()

    def get_service_credentials(self) -> Dict[str, str]:
        """Get OAuth credentials (from env or Secrets Manager)."""
        if self.environment == "local":
            return self._get_from_env()
        else:
            return self._get_from_secrets_manager()

    def _get_from_env(self) -> Dict[str, str]:
        """Get credentials from environment variables."""
        client_id = os.getenv("SERVICE_CLIENT_ID")
        client_secret = os.getenv("SERVICE_CLIENT_SECRET")

        if not client_id or not client_secret:
            raise ValueError(
                "SERVICE_CLIENT_ID and SERVICE_CLIENT_SECRET required. "
                "Copy .env.example to .env and configure."
            )

        return {"client_id": client_id, "client_secret": client_secret}

    def _get_from_secrets_manager(self) -> Dict[str, str]:
        """Get credentials from AWS Secrets Manager."""
        import boto3
        secret_name = "agent-name/credentials"
        region = self.get_aws_region()

        client = boto3.client("secretsmanager", region_name=region)
        response = client.get_secret_value(SecretId=secret_name)
        secret = json.loads(response["SecretString"])

        return {"client_id": secret["client_id"], "client_secret": secret["client_secret"]}

    def get_aws_region(self) -> str:
        """Get AWS region."""
        return os.getenv("AWS_REGION", "ap-southeast-2")
```

**Environment Patterns**:
- `local`: `.env` file with OAuth
- `dev`: `.env` file with OAuth
- `prod`: AWS Secrets Manager with OAuth

#### `src/constants/prompts.py`

**Purpose**: System prompts and tool descriptions

**Pattern**:
```python
"""System prompts and tool descriptions."""

# System prompt for the agent
SYSTEM_PROMPT = """You are a GitHub assistant. Use your tools to help users with repositories, issues, and pull requests.

**Available Capabilities:**
- Repository management: list, create, get details
- Issue tracking: list, create, update, close, comment
- Pull requests: create, list, merge

**Authentication:**
Authentication is handled automatically. Never ask users for tokens or credentials.

**Best Practices:**
- Always confirm actions before making destructive changes
- Provide clear, actionable feedback
- Use markdown formatting for readability
- Include relevant URLs in responses
"""

# Tool-specific descriptions (if needed for dynamic registration)
TOOL_DESCRIPTIONS = {
    "list_repos": "Lists all repositories for the authenticated user",
    "create_repo": "Creates a new GitHub repository",
    "list_issues": "Lists issues in a repository",
    "create_issue": "Creates a new issue in a repository",
}

# Agent configuration
AGENT_CONFIG = {
    "model_id": "anthropic.claude-3-5-sonnet-20241022-v2:0",
    "region": "ap-southeast-2",
    "temperature": 0.7,
}
```

#### `src/constants/messages.py`

**Purpose**: Standardized messages and templates

**Pattern**:
```python
"""Standardized messages and response templates."""

# Error messages
ERROR_AUTH_REQUIRED = "❌ Authentication required. Please authorize the app."
ERROR_NOT_FOUND = "❌ Resource not found: {resource}"
ERROR_PERMISSION_DENIED = "❌ Permission denied. Check OAuth scopes."
ERROR_API_ERROR = "❌ API error ({status}): {message}"
ERROR_NETWORK_ERROR = "❌ Network error: {message}"

# Success messages
SUCCESS_CREATED = "✅ Created {resource}: {name}\nURL: {url}"
SUCCESS_UPDATED = "✅ Updated {resource}: {name}"
SUCCESS_DELETED = "✅ Deleted {resource}: {name}"
SUCCESS_OPERATION = "✅ Operation completed: {details}"

# Info messages
INFO_INITIALIZING = "🔐 Initializing authentication..."
INFO_AUTHENTICATED = "✅ Authentication successful"
INFO_PROCESSING = "🚀 Processing request..."

# OAuth messages
OAUTH_REQUIRED_TEMPLATE = """🔐 Authorization Required

Please authorize the app:
{oauth_url}

After authorizing, try your request again.
"""
```

#### `src/utils/response.py`

**Purpose**: Response formatting and protocols

**Pattern**:
```python
"""Response formatting and protocols."""

from typing import Any, Dict, Literal, Optional
from pydantic import BaseModel, Field

class AgentResponse(BaseModel):
    """Standardized agent response format."""
    success: bool = Field(..., description="Whether operation succeeded")
    message: str = Field(..., description="Human-readable message")
    data: Dict[str, Any] = Field(default_factory=dict, description="Structured data")
    agent_type: str = Field(..., description="Agent identifier")
    error_code: Optional[str] = Field(None, description="Machine-readable error code")

def format_success(message: str, details: Optional[str] = None) -> str:
    """Format success message.

    Args:
        message: Main success message
        details: Optional additional details

    Returns:
        Formatted string with emoji
    """
    if details:
        return f"✅ {message}\n{details}"
    return f"✅ {message}"

def format_error(message: str, error_code: Optional[str] = None) -> str:
    """Format error message.

    Args:
        message: Error message
        error_code: Optional error code

    Returns:
        Formatted string with emoji
    """
    if error_code:
        return f"❌ Error [{error_code}]: {message}"
    return f"❌ {message}"

def format_info(message: str) -> str:
    """Format info message."""
    return f"ℹ️ {message}"

def format_client_text(text: str) -> Dict[str, Any]:
    """Format text for client streaming.

    Args:
        text: Text to format

    Returns:
        Formatted event dict for streaming
    """
    return {"type": "text", "text": text}
```

#### `src/utils/helpers.py`

**Purpose**: General utility functions

**Pattern**:
```python
"""General utility functions."""

from typing import Any, Dict

def extract_text_from_event(event: Dict[str, Any]) -> str:
    """Extract text from Strands streaming event.

    Handles multiple event formats.

    Args:
        event: Streaming event dict

    Returns:
        Extracted text or empty string
    """
    # Event format 1: {"type": "text", "text": "..."}
    if event.get("type") == "text":
        return event.get("text", "")

    # Event format 2: {"content": [{"type": "text", "text": "..."}]}
    if "content" in event:
        for item in event["content"]:
            if item.get("type") == "text":
                return item.get("text", "")

    return ""

def log_server(msg: str, level: str = "info"):
    """Server-side logging (not sent to client).

    Args:
        message: Log message
        level: "info", "success", "warning", "error"
    """
    emoji = {
        "info": "ℹ️",
        "success": "✅",
        "warning": "⚠️",
        "error": "❌",
    }
    print(f"{emoji.get(level, 'ℹ️')} [SERVER] {msg}")
```

#### `src/gateway/interface.py`

**Purpose**: Protocol-based authentication interface

**Pattern**:

```python
"""Gateway authentication interface for dependency injection."""

from typing import Protocol, runtime_checkable

@runtime_checkable
class GatewayAuth(Protocol):
    """Protocol for gateway authentication providers.

    This interface allows the agent to work with different authentication
    strategies without coupling to a specific implementation.
    Implementations include service-specific OAuth handlers (GitHub, JIRA, etc.)
    that integrate with AgentCore's OAuth flow.

    Uses structural subtyping (PEP 544) - any class implementing these
    methods is compatible without explicit inheritance.
    """

    async def get_token(self) -> str:
        """Get a valid access token.

        Returns:
            str: Service access token

        Raises:
            ValueError: If authentication incomplete or token invalid
        """
        ...

    def is_authenticated(self) -> bool:
        """Check if authentication is complete.

        Returns:
            bool: True if authenticated, False otherwise
        """
        ...
```

**Why Protocol Instead of ABC**:

- Structural subtyping (duck typing with type checking)
- No inheritance required
- More flexible for different implementations
- Modern Python pattern (PEP 544)

#### `src/gateway/agentcore.py`

**Purpose**: Production OAuth implementation with AgentCore

**Pattern**:

```python
"""AgentCore OAuth authentication."""

import asyncio
from typing import Callable, Optional

from bedrock_agentcore_starter_toolkit import CredentialProvider

class AgentCoreServiceAuth:
    """Production OAuth authentication via AgentCore.

    Handles OAuth 3-legged flow with user authorization.
    """

    def __init__(
        self,
        provider_name: str,
        oauth_url_callback: Optional[Callable[[str], None]] = None,
    ):
        """Initialize OAuth authentication.

        Args:
            provider_name: Credential provider name
            oauth_url_callback: Callback for OAuth URL streaming
        """
        self.provider_name = provider_name
        self.oauth_url_callback = oauth_url_callback
        self._token: Optional[str] = None
        self._pending_oauth_url: Optional[str] = None

    async def get_token(self) -> str:
        """Get access token, triggering OAuth if needed.

        Returns:
            str: Valid access token

        Raises:
            ValueError: If OAuth authorization incomplete
        """
        if self._token:
            return self._token

        # Initialize credential provider
        provider = CredentialProvider(name=self.provider_name)

        try:
            # This may trigger OAuth flow
            result = await asyncio.to_thread(provider.get_credential)

            if result.get("requiresAuthorization"):
                oauth_url = result["authorizationUrl"]
                self._pending_oauth_url = oauth_url

                # Stream OAuth URL immediately via callback
                if self.oauth_url_callback:
                    self.oauth_url_callback(oauth_url)

                raise ValueError(
                    f"User authorization required: {oauth_url}"
                )

            # Extract token
            self._token = result.get("accessToken")
            return self._token

        except Exception as e:
            raise ValueError(f"Authentication failed: {e}")

    def is_authenticated(self) -> bool:
        """Check if token is available.

        Returns:
            bool: True if token exists
        """
        return self._token is not None
```

**Key Features**:

- OAuth URL streaming via callback
- Token caching
- Error handling
- User authorization flow

#### `src/common/config.py`

**Purpose**: Configuration management (environment detection, credentials)

**Responsibilities**:

- Environment detection (local/dev/prod)
- Credential loading (env vars vs Secrets Manager)
- AWS region configuration
- Service-specific settings

**Pattern**:

```python
"""Configuration management."""

import json
import os
from typing import Dict
from dotenv import load_dotenv

def get_environment() -> str:
    """Get current environment from AGENT_ENV variable.

    Returns:
        str: "local", "dev", or "prod"
    """
    env = os.getenv("AGENT_ENV", "prod").lower()
    if env not in ["local", "dev", "prod"]:
        return "prod"
    return env

class Config:
    """Configuration manager."""

    def __init__(self, environment: str = "local"):
        """Initialize configuration.

        Args:
            environment: "local" or "production"
        """
        self.environment = environment

        if environment == "local":
            load_dotenv()

    def get_service_credentials(self) -> Dict[str, str]:
        """Get OAuth credentials.

        Returns:
            Dict with 'client_id' and 'client_secret'
        """
        if self.environment == "local":
            return self._get_from_env()
        else:
            return self._get_from_secrets_manager()

    def _get_from_env(self) -> Dict[str, str]:
        """Get credentials from environment variables."""
        client_id = os.getenv("SERVICE_CLIENT_ID")
        client_secret = os.getenv("SERVICE_CLIENT_SECRET")

        if not client_id or not client_secret:
            raise ValueError(
                "SERVICE_CLIENT_ID and SERVICE_CLIENT_SECRET required. "
                "Copy .env.example to .env and configure."
            )

        return {
            "client_id": client_id,
            "client_secret": client_secret,
        }

    def _get_from_secrets_manager(self) -> Dict[str, str]:
        """Get credentials from AWS Secrets Manager."""
        import boto3

        secret_name = "agent-name/credentials"
        region = self.get_aws_region()

        client = boto3.client("secretsmanager", region_name=region)
        response = client.get_secret_value(SecretId=secret_name)
        secret = json.loads(response["SecretString"])

        return {
            "client_id": secret["client_id"],
            "client_secret": secret["client_secret"],
        }

    def get_aws_region(self) -> str:
        """Get AWS region."""
        return os.getenv("AWS_REGION", "ap-southeast-2")
```

**Environment Patterns**:

- `local`: `.env` file with OAuth
- `dev`: `.env` file with OAuth
- `prod`: AWS Secrets Manager with OAuth

#### `src/common/utils.py`

**Purpose**: Shared utilities (response formatting, logging, helpers)

**Common Utilities**:

```python
"""Common utilities."""

from typing import Any, Dict
from pydantic import BaseModel

class AgentResponse(BaseModel):
    """Standardized agent response format."""
    success: bool
    message: str
    data: Dict[str, Any]
    agent_type: str

def format_client_text(text: str) -> Dict[str, Any]:
    """Format text for client streaming.

    Args:
        text: Text to format

    Returns:
        Formatted event dict
    """
    return {
        "type": "text",
        "text": text,
    }

def log_server_message(message: str, level: str = "info"):
    """Server-side logging (not sent to client).

    Args:
        message: Log message
        level: "info", "success", "warning", "error"
    """
    emoji = {
        "info": "ℹ️",
        "success": "✅",
        "warning": "⚠️",
        "error": "❌",
    }
    print(f"{emoji.get(level, 'ℹ️')} [SERVER] {message}")

def extract_text_from_event(event: Dict[str, Any]) -> str:
    """Extract text from streaming event.

    Handles multiple event formats from Strands.

    Args:
        event: Streaming event dict

    Returns:
        Extracted text or empty string
    """
    # Event format 1: {"type": "text", "text": "..."}
    if event.get("type") == "text":
        return event.get("text", "")

    # Event format 2: {"content": [{"type": "text", "text": "..."}]}
    if "content" in event:
        for item in event["content"]:
            if item.get("type") == "text":
                return item.get("text", "")

    return ""
```

#### `src/tools/resource.py`

**Purpose**: Tool implementations for specific resources

**Pattern (Function Tools with Closures)**:

```python
"""Resource tools - Following Strands function pattern."""

import httpx
from strands import tool
from typing import Sequence

from src.auth import ServiceAuth

def resource_tools(auth: ServiceAuth) -> Sequence:
    """Create resource tools with auth closure.

    Factory function that returns tools with auth captured in closure.
    This is the modern Strands pattern (not class-based tools).

    Args:
        auth: ServiceAuth implementation

    Returns:
        Sequence of tool functions
    """

    @tool
    async def list_resources(filter: str = "all") -> str:
        """List resources from service.

        Args:
            filter: Filter type ("all", "active", "archived")

        Returns:
            Formatted string with resource information
        """
        token = await auth.get_token()
        headers = {"Authorization": f"Bearer {token}"}

        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.service.com/resources",
                headers=headers,
                params={"filter": filter},
                timeout=30.0,
            )
            response.raise_for_status()
            resources = response.json()

            if not resources:
                return f"No {filter} resources found."

            # Format response
            result_lines = [f"Resources ({filter}):\n"]
            for res in resources:
                result_lines.append(f"• {res['name']} - {res['status']}")

            return "\n".join(result_lines)

    @tool
    async def create_resource(name: str, config: str) -> str:
        """Create a new resource.

        Args:
            name: Resource name
            config: Configuration JSON string

        Returns:
            Success message with resource URL
        """
        token = await auth.get_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.service.com/resources",
                headers=headers,
                json={"name": name, "config": config},
                timeout=30.0,
            )
            response.raise_for_status()
            resource = response.json()

            return f"✅ Created resource: {resource['name']}\nURL: {resource['url']}"

    # Return all tools
    return [list_resources, create_resource]
```

**Key Patterns**:

- Factory function returns sequence of tools
- Auth captured in closure (no class state)
- Async tools with `httpx`
- Type hints for LLM understanding
- Detailed docstrings (used by LLM)
- Error handling with meaningful messages

#### `src/__init__.py` - Clean Imports

**Purpose**: Enable clean imports across the project

**Pattern**:
```python
"""Agent package with clean imports."""

# Main entrypoints
from .runtime import app as agentcore_app
from .main import main as strands_main

# Agent factory
from .agent import create_agent

# Gateway
from .gateway.interface import GatewayAuth
from .gateway.agentcore import AgentCoreAuth

# Utils
from .utils.response import AgentResponse, format_success, format_error
from .utils.helpers import extract_text_from_event, log_server

# Constants
from .constants.prompts import SYSTEM_PROMPT
from .constants.messages import (
    ERROR_AUTH_REQUIRED,
    ERROR_NOT_FOUND,
    SUCCESS_CREATED,
)

__all__ = [
    # Entrypoints
    "agentcore_app",
    "strands_main",
    # Core
    "create_agent",
    # Gateway
    "GatewayAuth",
    "AgentCoreAuth",
    # Utils
    "AgentResponse",
    "format_success",
    "format_error",
    "extract_text_from_event",
    "log_server",
    # Constants
    "SYSTEM_PROMPT",
    "ERROR_AUTH_REQUIRED",
    "ERROR_NOT_FOUND",
    "SUCCESS_CREATED",
]
```

**Benefits**:
```python
# Clean imports from anywhere in the project
from src import create_agent, AgentCoreAuth
from src import format_success, SYSTEM_PROMPT

# No more relative import issues
# No more: from src.gateway.agentcore import AgentCoreAuth
# Just: from src import AgentCoreAuth
```

---

**Pattern**:

```python
"""Response protocol for consistent agent responses."""

from typing import Any, Dict, Literal, Optional
from pydantic import BaseModel, Field

class AgentResponse(BaseModel):
    """Standardized agent response format.

    All agents should return responses in this format for consistency.
    """

    success: bool = Field(
        ...,
        description="Whether the operation succeeded"
    )

    message: str = Field(
        ...,
        description="Human-readable message"
    )

    data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Structured data payload"
    )

    agent_type: str = Field(
        ...,
        description="Agent identifier (github, jira, etc.)"
    )

    error_code: Optional[str] = Field(
        None,
        description="Machine-readable error code if failed"
    )

class OAuthRequiredResponse(AgentResponse):
    """Response indicating OAuth authorization needed."""

    success: Literal[False] = False
    oauth_url: str = Field(
        ...,
        description="OAuth authorization URL"
    )
    requires_authorization: Literal[True] = True

def create_success_response(
    message: str,
    data: Dict[str, Any],
    agent_type: str,
) -> AgentResponse:
    """Create success response.

    Args:
        message: Success message
        data: Response data
        agent_type: Agent identifier

    Returns:
        AgentResponse instance
    """
    return AgentResponse(
        success=True,
        message=message,
        data=data,
        agent_type=agent_type,
    )

def create_error_response(
    message: str,
    agent_type: str,
    error_code: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
) -> AgentResponse:
    """Create error response.

    Args:
        message: Error message
        agent_type: Agent identifier
        error_code: Optional error code
        data: Optional error details

    Returns:
        AgentResponse instance
    """
    return AgentResponse(
        success=False,
        message=message,
        data=data or {},
        agent_type=agent_type,
        error_code=error_code,
    )
```

---

## Dependencies & Tooling

### Core Dependencies

#### Runtime Dependencies

```toml
[project]
dependencies = [
    # AgentCore & Strands
    "bedrock-agentcore[strands-agents]>=0.1.0",
    "bedrock-agentcore-starter-toolkit>=0.1.0",
    "strands-agents>=0.1.0",

    # AWS
    "boto3>=1.39.15",

    # HTTP & APIs
    "httpx>=0.27.0",        # Async HTTP client (preferred over requests)

    # CLI & Config
    "typer>=0.12.0",        # CLI framework
    "python-dotenv>=1.0.0", # Environment variables

    # Task Runner
    "poethepoet>=0.24.0",   # Task automation

    # Data Validation
    "pydantic>=2.0.0",      # Type-safe data models

    # Service-Specific
    # Add service SDKs here (e.g., jira>=3.5.0)
]
```

#### Development Dependencies

```toml
[project.optional-dependencies]
dev = [
    "mypy>=1.0.0",          # Static type checking
    "isort>=5.12.0",        # Import sorting
    "black>=23.0.0",        # Code formatting
]
```

### Package Manager: `uv`

**Why `uv`**:

- 10-100x faster than pip
- Built-in virtual environment management
- Compatible with pip/setuptools
- Lock file for reproducibility

**Installation**:

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or via pip
pip install uv
```

**Common Commands**:

```bash
# Create virtual environment
uv venv

# Activate (optional with uv)
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Install dependencies
uv pip install -e .         # Editable install
uv pip install -e ".[dev]"  # With dev dependencies

# Add dependency
uv pip install httpx
# Then add to pyproject.toml

# Sync from pyproject.toml
uv pip sync

# Run command in venv (without activation)
uv run python script.py
uv run python -m src.main
```

### Code Quality Tools

#### Black (Code Formatter)

**Configuration** (in `pyproject.toml`):

```toml
[tool.black]
line-length = 88
target-version = ["py310"]
```

**Usage**:

```bash
# Format all files
black src/

# Check without modifying
black --check src/

# Format single file
black src/agent.py
```

#### isort (Import Sorting)

**Configuration** (in `pyproject.toml`):

```toml
[tool.isort]
profile = "black"
multi_line_output = 3
line_length = 88
known_first_party = ["src"]
```

**Usage**:

```bash
# Sort imports
isort src/

# Check only
isort --check src/
```

#### mypy (Type Checking)

**Configuration** (in `pyproject.toml`):

```toml
[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
ignore_missing_imports = true
```

**Usage**:

```bash
# Type check
mypy src/

# Check specific file
mypy src/agent.py
```

### Task Runner: poethepoet

**Why poethepoet**:

- Simple task runner in pyproject.toml
- No need for Makefile
- Cross-platform compatibility

**Configuration** (in `pyproject.toml`):

```toml
[tool.poe.tasks]
# Development
dev = "python -m src.runtime"
lint = "black --check src/ && isort --check src/ && mypy src/"
format = "black src/ && isort src/"

# AgentCore
invoke = "agentcore invoke"
launch = "agentcore launch"
deploy = "agentcore deploy"
logs = "agentcore logs --follow"

# Docker
build = "docker build -t agent-name:latest ."
run = "docker run -p 9000:9000 agent-name:latest"
```

**Usage**:

```bash
# Run tasks
poe dev      # Start local runtime
poe lint     # Check code quality
poe format   # Format code

# Or with uv
uv run poe dev
```

---

## Architecture Patterns

### 1. Dependency Injection Pattern

**Why**: Flexibility, separation of concerns, maintainability

**Implementation**:

```python
# Define Protocol interface
@runtime_checkable
class ServiceAuth(Protocol):
    async def get_token(self) -> str: ...
    def is_authenticated(self) -> bool: ...

# Implement for your service
class AgentCoreServiceAuth:
    async def get_token(self) -> str:
        # Real OAuth flow via AgentCore
        ...

# Inject into agent
def create_agent(auth: ServiceAuth) -> Agent:
    return Agent(
        tools=[*tools(auth)],  # Tools receive auth
        ...
    )

# Use in your agent
agent = create_agent(AgentCoreServiceAuth("provider"))
```

**Benefits**:

- Flexible authentication implementations
- Service-specific OAuth handlers
- Clean separation of concerns
- Type-safe with Protocol

### 2. Function Tools with Closures

**Why**: Stateless, composable, modern Strands pattern

**Implementation**:

```python
def resource_tools(auth: ServiceAuth) -> Sequence:
    """Factory returns tools with auth in closure."""

    @tool
    async def list_items() -> str:
        token = await auth.get_token()  # Auth from closure
        # Make API call
        ...

    @tool
    async def create_item(name: str) -> str:
        token = await auth.get_token()  # Auth from closure
        # Make API call
        ...

    return [list_items, create_item]

# Usage in agent
agent = Agent(
    tools=[
        *resource1_tools(auth),
        *resource2_tools(auth),
    ]
)
```

**Benefits**:

- No class state
- Auth captured in closure
- Easy to test
- Composable

**Anti-pattern** (Old Strands pattern):

```python
# DON'T DO THIS - class-based tools are outdated
class ResourceTool:
    def __init__(self, auth):
        self.auth = auth

    @tool
    def list_items(self):
        ...
```

### 3. Separation of Concerns

**Three Layers**:

1. **Runtime Layer** (`runtime.py`)

   - AgentCore integration
   - OAuth streaming
   - Deployment configuration
   - Infrastructure concerns

2. **Agent Layer** (`agent.py`)

   - Pure agent logic
   - Tool assembly
   - System prompts
   - Testable without deployment

3. **Tool Layer** (`tools/*.py`)
   - API interactions
   - Business logic
   - Data formatting
   - Resource operations

**Flow**:

```
User Request
    ↓
runtime.py (infrastructure)
    ↓
agent.py (orchestration)
    ↓
tools/*.py (operations)
    ↓
External APIs
```

### 4. Protocol Over ABC

**Why Protocol**:

- Structural subtyping (duck typing with types)
- No inheritance required
- More flexible
- Modern Python (PEP 544)

**Protocol**:

```python
@runtime_checkable
class ServiceAuth(Protocol):
    async def get_token(self) -> str: ...

# Any class with this method signature works
class MyAuth:
    async def get_token(self) -> str:
        return "token"

# No need for: class MyAuth(ServiceAuth)
# Structural compatibility is enough
```

**ABC** (Old pattern):

```python
# DON'T DO THIS
from abc import ABC, abstractmethod

class ServiceAuth(ABC):
    @abstractmethod
    async def get_token(self) -> str:
        pass

# Requires explicit inheritance
class MyAuth(ServiceAuth):
    ...
```

### 5. Async-First with httpx

**Why httpx**:

- Async support
- HTTP/2 support
- Modern API
- Better than `requests`

**Pattern**:

```python
import httpx

@tool
async def api_call() -> str:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.example.com/endpoint",
            headers={"Authorization": f"Bearer {token}"},
            params={"key": "value"},
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()
        return format_response(data)
```

**Error Handling**:

```python
try:
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
except httpx.HTTPStatusError as e:
    return f"❌ API error ({e.response.status_code}): {e.response.text}"
except httpx.RequestError as e:
    return f"❌ Network error: {str(e)}"
```

---

## Development Workflow

### Initial Setup

1. **Create agent directory**:

   ```bash
   mkdir agents/new-agent
   cd agents/new-agent
   ```

2. **Create basic structure**:

   ```bash
   mkdir -p src/{gateway,constants,utils,tools} docs scripts
   touch src/{__init__.py,runtime.py,main.py,agent.py,config.py}
   touch src/gateway/{__init__.py,interface.py,agentcore.py}
   touch src/constants/{__init__.py,prompts.py,messages.py}
   touch src/utils/{__init__.py,response.py,helpers.py}
   touch src/tools/__init__.py
   touch pyproject.toml Dockerfile .env.example .gitignore
   ```

3. **Initialize pyproject.toml**:

   ```toml
   # Copy from template above and customize
   ```

4. **Create virtual environment**:

   ```bash
   uv venv
   source .venv/bin/activate  # Linux/Mac
   uv pip install -e ".[dev]"
   ```

5. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

### Development Modes

#### Mode 1: Local Runtime (Hot Reload)

**Purpose**: Local development with Bedrock model and OAuth

**Setup**:

```bash
export AGENT_ENV=local
export AWS_PROFILE=your-profile  # For Bedrock access
```

**Run**:

```bash
# Start runtime (auto-reloads on file changes with watchdog)
uv run python -m src.runtime

# Or with poe task
poe dev
```

**Hot Reload Implementation**:

```python
# runtime.py - add for development
if __name__ == "__main__":
    import sys

    # Check if in development mode
    if "--dev" in sys.argv or os.getenv("AGENT_ENV") == "local":
        try:
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler

            class ReloadHandler(FileSystemEventHandler):
                def on_modified(self, event):
                    if event.src_path.endswith(".py"):
                        print(f"🔄 File changed: {event.src_path}")
                        # Reload modules
                        import importlib
                        importlib.reload(...)

            observer = Observer()
            observer.schedule(ReloadHandler(), "src", recursive=True)
            observer.start()
            print("🔥 Hot reload enabled")
        except ImportError:
            print("⚠️ watchdog not installed, hot reload disabled")

    app.run()
```

**Install watchdog**:

```bash
uv pip install watchdog
```

#### Mode 2: AgentCore Local

**Purpose**: Test full AgentCore integration locally

**Setup**:

```bash
export AGENT_ENV=local
```

**Run**:

```bash
# Terminal 1: Start agent
agentcore launch --local

# Terminal 2: Invoke agent
agentcore invoke \
    --user-id test-user \
    --message "What can you do?"
```

**With OAuth**:

```bash
export AGENT_ENV=dev  # Enable real OAuth
agentcore launch --local
agentcore invoke --user-id your-github-username --message "test"
# Follow OAuth URL in output
```

#### Mode 3: Production Deployment

**Purpose**: Deploy to AWS with full OAuth

**Setup**:

```bash
# Ensure AWS credentials configured
aws sso login --profile your-profile
export AWS_PROFILE=your-profile
```

**Deploy**:

```bash
# First time: Create resources
agentcore deploy

# Updates: Deploy code changes
agentcore deploy

# View logs
agentcore logs --follow

# Invoke
agentcore invoke \
    --user-id production-user \
    --message "List items"
```

### Development Cycle

**Typical workflow**:

1. **Local runtime** (with hot reload):

   ```bash
   poe dev
   # Make changes, see results immediately
   ```

2. **AgentCore local**:

   ```bash
   agentcore launch --local
   agentcore invoke --user-id test --message "test"
   ```

3. **Deploy**:
   ```bash
   agentcore deploy
   agentcore logs --follow
   ```

**Time Investment**:

- Local runtime: < 30 seconds startup
- AgentCore local: ~1 minute
- Production deploy: ~3-5 minutes

**Iteration Speed**:

- Hot reload for instant feedback during development
- Local AgentCore testing before deployment
- Deploy when ready for production

---

## Best Practices

### 1. Type Hints Everywhere

**Why**: Better IDE support, early error detection, LLM understanding

**Pattern**:

```python
# Good
async def get_items(
    filter: str = "all",
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """Get items with type-safe parameters."""
    ...

# Bad
async def get_items(filter="all", limit=10):
    """Get items without types."""
    ...
```

### 2. Detailed Docstrings

**Why**: LLM uses docstrings to understand tool usage

**Pattern**:

```python
@tool
async def create_resource(
    name: str,
    description: str,
    visibility: str = "private",
) -> str:
    """Create a new resource.

    Creates a resource with the specified configuration.
    Resources are created asynchronously and may take a few moments
    to become fully available.

    Args:
        name: Resource name (3-50 characters, alphanumeric)
        description: Resource description (max 500 characters)
        visibility: Resource visibility ("public", "private", or "internal")

    Returns:
        Success message with resource URL and ID

    Raises:
        ValueError: If name is invalid or already exists

    Example:
        >>> await create_resource(
        ...     name="my-resource",
        ...     description="Test resource",
        ...     visibility="private"
        ... )
        "✅ Created resource: my-resource\\nURL: https://..."
    """
    ...
```

### 3. Consistent Response Formats

**Why**: Easier for LLM to parse and users to understand

**Pattern**:

```python
# Success
return "✅ Operation completed: Details here"

# Error
return "❌ Error: Clear error message"

# Info
return "ℹ️ Information: Details"

# With structured data
return """✅ Resource created
Name: my-resource
URL: https://...
ID: abc123
"""
```

### 4. Environment Variables for Config

**Why**: 12-factor app, secure credentials, environment flexibility

**Pattern**:

```python
# .env.example
AGENT_ENV=local
SERVICE_CLIENT_ID=your_client_id
SERVICE_CLIENT_SECRET=your_client_secret
AWS_REGION=ap-southeast-2

# Load in code
from dotenv import load_dotenv
load_dotenv()

client_id = os.getenv("SERVICE_CLIENT_ID")
```

### 5. Error Handling with Context

**Why**: Help users and LLM understand what went wrong

**Pattern**:

```python
try:
    response = await client.get(url)
    response.raise_for_status()
except httpx.HTTPStatusError as e:
    status = e.response.status_code

    if status == 401:
        return "❌ Authentication failed. Token may be expired."
    elif status == 403:
        return "❌ Permission denied. Check OAuth scopes."
    elif status == 404:
        return f"❌ Resource not found: {resource_name}"
    else:
        return f"❌ API error ({status}): {e.response.text}"

except httpx.RequestError as e:
    return f"❌ Network error: {str(e)}"
```

### 6. Logging for Debugging

**Why**: Debug production issues, understand flow

**Pattern**:

```python
# Server-side logging (not sent to client)
def log_server(msg: str, level: str = "info"):
    """Log server-side messages."""
    emoji = {"info": "ℹ️", "success": "✅", "error": "❌"}
    print(f"{emoji.get(level)} [SERVER] {msg}")

# Usage
log_server("Starting OAuth flow", "info")
log_server(f"Token obtained: {token[:10]}...", "success")
log_server(f"API error: {error}", "error")

# Client messages (sent to user)
yield format_client_text("🔐 Authenticating...")
yield format_client_text("✅ Authentication successful")
```

### 7. Separation of Auth and Tools

**Why**: Testability, clarity, reusability

**Pattern**:

```python
# DON'T: Tools that handle their own auth
@tool
async def list_items():
    # Figure out auth somehow
    token = get_token_somehow()
    ...

# DO: Tools receive auth via closure
def tools_factory(auth: ServiceAuth) -> Sequence:
    @tool
    async def list_items():
        token = await auth.get_token()  # Clear dependency
        ...
    return [list_items]
```

### 8. Pre-commit Hooks

**Why**: Catch issues before commit

**Setup** (`.pre-commit-config.yaml`):

```yaml
repos:
  - repo: local
    hooks:
      - id: black
        name: black
        entry: black
        language: system
        types: [python]

      - id: isort
        name: isort
        entry: isort
        language: system
        types: [python]

      - id: mypy
        name: mypy
        entry: mypy
        language: system
        types: [python]
```

**Install**:

```bash
pip install pre-commit
pre-commit install
```

### 9. Documentation as Code

**Why**: Keep docs synchronized with code

**Pattern**:

```markdown
# README.md (generated from code inspection)

## Available Tools

<!-- AUTO-GENERATED: DO NOT EDIT -->

- list_resources(filter: str) - List all resources
- create_resource(name: str, config: str) - Create new resource
<!-- END AUTO-GENERATED -->
```

**Generator**:

```python
# docs/generate_tool_docs.py
"""Generate tool documentation from code."""

import inspect
from src.agent import create_agent
from src.gateway import AgentCoreAuth

def generate_tool_docs():
    # Use real auth for documentation generation
    auth = AgentCoreAuth("provider-name")
    agent = create_agent(auth)

    docs = ["## Available Tools\n"]
    for tool in agent.tools:
        sig = inspect.signature(tool)
        doc = tool.__doc__.split("\n")[0]
        docs.append(f"- {tool.__name__}{sig} - {doc}")

    return "\n".join(docs)
```

---

## AgentCore Integration

### Deployment Configuration

**File**: `.bedrock_agentcore.yaml`

**Initial Creation**:

```bash
# AgentCore creates this on first deploy
agentcore deploy

# File is auto-populated with:
# - Agent IDs
# - AWS ARNs
# - Memory IDs
# - OAuth configuration
```

**Key Sections**:

1. **Agent Configuration**:

```yaml
agents:
  agent-name:
    name: agent-name
    entrypoint: src/runtime.py
    platform: linux/arm64
    container_runtime: docker
```

2. **AWS Configuration**:

```yaml
aws:
  execution_role: arn:aws:iam::ACCOUNT:role/...
  account: 'ACCOUNT_ID'
  region: ap-southeast-2
  ecr_repository: ACCOUNT.dkr.ecr.REGION.amazonaws.com/repo
```

3. **Memory Configuration**:

```yaml
memory:
  mode: STM_ONLY # or LTM_ONLY or BOTH
  memory_id: agent_mem-...
  event_expiry_days: 30
```

4. **OAuth Configuration**:

```yaml
oauth_configuration:
  workload_name: agent-name
  credential_providers:
    - provider-name
```

### OAuth Provider Setup

**Create provider** (one-time setup):

```bash
# Run setup script
./scripts/setup_provider.sh

# Or manually with AWS CLI
aws bedrock-agentcore create-credential-provider \
    --name "github-provider" \
    --oauth-config '{
        "clientId": "YOUR_CLIENT_ID",
        "clientSecretArn": "arn:aws:secretsmanager:...",
        "authorizationEndpoint": "https://github.com/login/oauth/authorize",
        "tokenEndpoint": "https://github.com/login/oauth/access_token",
        "scopes": ["repo", "read:user"]
    }' \
    --region ap-southeast-2
```

**Register with agent**:

```bash
agentcore register-credential-provider \
    --agent-name agent-name \
    --provider-name provider-name
```

### Deployment Commands

**Common Operations**:

```bash
# Create/update deployment
agentcore deploy

# Deploy specific agent
agentcore deploy --agent-name agent-name

# Local testing
agentcore launch --local

# Invoke agent
agentcore invoke \
    --user-id username \
    --message "Your prompt here"

# View logs
agentcore logs --follow

# View memory
agentcore memory list
agentcore memory get --event-id xxx

# Delete agent (cleanup)
agentcore delete --agent-name agent-name
```

### Memory Management

**Memory Modes**:

- `STM_ONLY`: Short-term memory only (recent conversation)
- `LTM_ONLY`: Long-term memory only (persistent facts)
- `BOTH`: Both short-term and long-term

**Access Memory in Code**:

```python
from bedrock_agentcore_starter_toolkit import Memory

# Get conversation history
memory = Memory()
history = memory.get_conversation_history()

# Store fact
memory.store_fact("user_preference", {"theme": "dark"})

# Query facts
facts = memory.query_facts("user_preference")
```

### Observability

**Enable Logging**:

```yaml
# .bedrock_agentcore.yaml
observability:
  enabled: true
  log_level: INFO # DEBUG, INFO, WARNING, ERROR
```

**View Logs**:

```bash
# Tail logs
agentcore logs --follow

# Filter by level
agentcore logs --level ERROR

# Time range
agentcore logs --since 1h
```

**Custom Metrics** (optional):

```python
from aws_embedded_metrics import metric_scope

@metric_scope
def tool_with_metrics(metrics):
    metrics.put_metric("ToolExecutions", 1, "Count")
    metrics.set_property("ToolName", "list_items")
    # ... tool logic
```

---

## Quick Reference

### Project Setup

```bash
# Create structure
mkdir -p agents/new-agent/src/{auth,common,tools}

# Initialize environment
cd agents/new-agent
uv venv
uv pip install -e ".[dev]"
cp .env.example .env
```

### Development

```bash
# Local runtime (hot reload)
export AGENT_ENV=local
uv run python -m src.runtime

# AgentCore local
agentcore launch --local

# Deploy
agentcore deploy
```

### Code Quality

```bash
# Format
black src/
isort src/

# Type check
mypy src/
```

### Common Patterns

**Tool Definition**:

```python
def tools_factory(auth: ServiceAuth) -> Sequence:
    @tool
    async def tool_name(param: str) -> str:
        """Tool description."""
        token = await auth.get_token()
        # Implementation
        return result
    return [tool_name]
```

**Agent Factory**:

```python
def create_agent(auth: ServiceAuth) -> Agent:
    model = BedrockModel(model_id=MODEL_ID, region_name=REGION)
    return Agent(
        model=model,
        tools=[*tools_factory(auth)],
        system_prompt="...",
    )
```

**Response Format**:

```python
return "✅ Success: Details"
return "❌ Error: Details"
return "ℹ️ Info: Details"
```

---

## Troubleshooting

### Import Errors

```bash
# Check PYTHONPATH
echo $PYTHONPATH  # Should include project root

# Reinstall
uv pip install -e .

# Test imports manually
uv run python -c "from src import agent, runtime"
```

### OAuth Issues

```bash
# Check provider
aws bedrock-agentcore describe-credential-provider \
    --name provider-name

# Test OAuth locally
export AGENT_ENV=dev
agentcore launch --local
```

### Docker Build Failures

```bash
# Check PYTHONPATH in Dockerfile
ENV PYTHONPATH=/app

# Test build locally
docker build -t test:latest .
docker run --rm test:latest python -c "import src"
```

### Memory Issues

```bash
# Clear memory
agentcore memory clear --agent-name agent-name

# Check memory mode
cat .bedrock_agentcore.yaml | grep memory -A 5
```

---

## Summary

This guide establishes replicable patterns for building production-quality AWS Bedrock AgentCore agents:

✅ **Standard Structure**: Consistent folder organization across agents
✅ **Modern Python**: Type hints, async, protocols, latest tooling
✅ **Testability**: Architecture tests without AWS, incremental integration
✅ **Hot Reload**: Fast iteration cycles during development
✅ **Separation of Concerns**: Runtime vs agent vs tools
✅ **Dependency Injection**: Protocol-based auth for flexibility
✅ **Best Practices**: Code quality, error handling, documentation

**Key Takeaways**:

- Start with architecture tests (< 5 seconds)
- Use hot reload for fast development
- Test locally 90% of the time
- Deploy only when ready for integration
- Follow the patterns for consistency

**Next Steps**:

1. Use this guide as a template for new agents
2. Replicate the folder structure
3. Follow the development workflow
4. Test incrementally (architecture → local → deployed)
5. Maintain consistency across agents

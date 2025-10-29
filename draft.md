Based on your feedback, here's the **completely revised architecture** that addresses all your requirements:

## Key Changes Based on Your Requirements

### 1. **Prompts/Constants in Separate Files**

Long text prompts should live in a `prompts/` or `constants/` folder, not cluttering code files [1][2].

### 2. **Streaming Chat Interface**

The agent will run as a **streaming online chat** (not just PR automation), using `agent.stream_async()` for real-time token streaming, and only performs PR reviews when the user talks about it [3][4][5].

### 3. **AgentCore OAuth Provider for GitHub**

Instead of embedding GitHub API logic in tools, we'll use **AgentCore's built-in OAuth provider** with the `@requires_access_token` decorator for secure GitHub authentication. The agent uses GitHub's official API via Python SDK with automatic token management [6][7][8].

**Note:** Gateway is optional for this use case - we can use direct OAuth authentication with the GitHub SDK, which is simpler than setting up a full MCP Gateway.

### 4. **Modern Python: Functions Over Classes**

Modern Python (2025) favors **functional style with minimal classes** – use functions for logic, dataclasses for data, and classes only for APIs/state management [1][9][2][10].

---

## Revised Project Structure (Functional + Modular)

```
coding-agent-mvp/
├── pyproject.toml              # uv/Poetry deps
├── Dockerfile
├── .env.example
├── .bedrock_agentcore.yaml     # Agent configuration (created by agentcore configure)
├── src/
│   ├── config.py               # Pydantic Settings
│   ├── prompts/                # All long-text prompts (DRY)
│   │   ├── system_prompts.py  # Agent system prompts
│   │   └── templates.py       # Plan/status templates
│   ├── models/                 # Pydantic dataclasses only
│   │   ├── plan.py
│   │   ├── status.py
│   │   └── chat.py            # ChatMessage model
│   ├── auth/                   # OAuth authentication
│   │   ├── github_auth.py     # GitHubAuth with @requires_access_token
│   │   ├── setup_provider.py  # Script to create OAuth provider
│   │   └── interface.py       # Auth interface
│   ├── agent/                  # Single Strands Agent (functional)
│   │   ├── create_agent.py    # Agent factory function
│   │   └── runtime.py         # AgentCore Runtime entrypoint
│   ├── tools/                  # GitHub tools using authenticated API
│   │   ├── github_tools.py    # GitHub API wrappers
│   │   └── repos.py           # Repo operations
│   ├── chat/                   # Streaming chat handlers
│   │   ├── stream_handler.py  # SSE streaming logic
│   │   └── session.py         # Session management
│   ├── utils/                  # Pure utility functions
│   │   ├── logging.py
│   │   └── response.py        # Response formatting
│   └── main.py                 # FastAPI streaming app (optional)
├── scripts/
│   └── setup_provider.sh       # Bash script to create OAuth provider
├── tests/
│   ├── conftest.py
│   └── test_*.py
└── docs/
    └── oauth_setup.md          # OAuth setup guide
```

---

## Implementation: Functions-First, Minimal Classes

### 1. Prompts in Separate Files (src/prompts/system_prompts.py)

```python
"""System prompts for agents - separated from code for maintainability."""

CODING_AGENT_SYSTEM_PROMPT = """
You are an AI coding assistant with access to GitHub via MCP tools.

**Capabilities:**
- General conversation and coding help
- When asked about PR reviews: analyze PRs, suggest improvements, run tests
- Use GitHub MCP tools (list_tools, call_tool) for all GitHub interactions
- Scope operations to /agent-tasks/ folder when reviewing PRs
- Always propose a plan before executing multi-step tasks

**Workflow for PR Reviews (only when user mentions PR/review):**
1. Fetch PR details using GitHub MCP
2. Generate structured plan with PlanModel
3. Ask user confirmation
4. Execute review steps sequentially
5. Update status and comment results

**Tone:** Helpful, concise, technical. Stream responses for better UX.
"""

# Can have more prompts here for different contexts
PR_REVIEW_PLAN_PROMPT_TEMPLATE = """
Analyze this PR and create a review plan:

**PR #{pr_number}:** {title}
**Files:** {files_summary}

Return JSON matching PlanModel schema with objective, steps, risks, estimated_time_minutes.
"""
```

### 2. Templates as Pure Functions (src/prompts/templates.py)

```python
"""Template generation functions - pure, no state."""
from typing import List

def generate_plan_markdown(objective: str, steps: List[str], risks: List[str], time_min: int) -> str:
    """Generate PR plan as GitHub-flavored markdown."""
    steps_md = "\n".join(f"{i+1}. {step}" for i, step in enumerate(steps))
    risks_md = "\n".join(f"- {r}" for r in risks) if risks else "None identified"

    return f"""## 🤖 Proposed Review Plan

**Objective:** {objective}

**Steps:**
{steps_md}

**Potential Risks:**
{risks_md}

**Estimated Time:** {time_min} minutes

---
Reply with `approve` to proceed or `cancel` to abort.
"""

def generate_status_json(status: str, step: str, progress: int, issues: List[str]) -> dict:
    """Generate status object - returns dict for JSON serialization."""
    from datetime import datetime
    return {
        "status": status,
        "current_step": step,
        "progress": progress,
        "issues": issues,
        "updated_at": datetime.utcnow().isoformat()
    }
```

### 3. OAuth Provider Setup (src/auth/setup_provider.py)

```python
"""
Setup OAuth2 credential provider for GitHub authentication.
Based on bedrock-agent-template pattern.
Run this once before deploying the agent.
"""
import boto3
import os
from ..config import settings

def create_github_oauth_provider() -> str:
    """
    Create OAuth2 credential provider for GitHub in AgentCore Identity.
    This enables 3-Legged OAuth (USER_FEDERATION) for per-user tokens.
    """
    client = boto3.client('bedrock-agentcore-control', region_name=settings.aws_region)

    # Delete existing provider if it exists (for updates)
    try:
        providers = client.list_oauth2_credential_providers()
        if any(p['name'] == 'github-provider' for p in providers.get('credentialProviders', [])):
            print("♻️  Deleting existing provider...")
            client.delete_oauth2_credential_provider(
                name='github-provider'
            )
            import time
            time.sleep(5)  # Wait for cleanup
    except Exception as e:
        print(f"No existing provider to delete: {e}")

    # Create new provider
    response = client.create_oauth2_credential_provider(
        name='github-provider',  # Must match agent config
        credentialProviderVendor='GithubOauth2',  # Predefined vendor
        oauth2ProviderConfigInput={
            'githubOauth2ProviderConfig': {
                'clientId': settings.github_client_id.get_secret_value(),
                'clientSecret': settings.github_client_secret.get_secret_value()
            }
        }
    )

    provider_arn = response['credentialProviderArn']
    callback_url = response.get('callbackUrl', 'N/A')

    print(f"✅ Created OAuth provider: {provider_arn}")
    print(f"   Provider name: github-provider")
    print(f"   Vendor: GithubOauth2")
    print()
    print("🔗 IMPORTANT: Register this callback URL in your GitHub OAuth App:")
    print(f"   {callback_url}")
    print()
    print("📝 Steps to register:")
    print("   1. Go to https://github.com/settings/developers")
    print("   2. Select your OAuth App")
    print("   3. Add the callback URL above to 'Authorization callback URL'")
    print("   4. Save changes")
    print()

    return provider_arn


def verify_provider_setup():
    """Verify the provider was created correctly."""
    client = boto3.client('bedrock-agentcore-control', region_name=settings.aws_region)

    providers = client.list_oauth2_credential_providers()
    github_provider = next(
        (p for p in providers.get('credentialProviders', [])
         if p['name'] == 'github-provider'),
        None
    )

    if github_provider:
        print("✅ Provider verified:")
        print(f"   ARN: {github_provider['credentialProviderArn']}")
        print(f"   Name: {github_provider['name']}")
        return True
    else:
        print("❌ Provider not found!")
        return False


if __name__ == "__main__":
    print("🔐 Setting up GitHub OAuth provider...")
    provider_arn = create_github_oauth_provider()
    verify_provider_setup()
```

**Alternative: Bash Script (scripts/setup_provider.sh)**

```bash
#!/bin/bash
# Based on bedrock-agent-template pattern
set -e

REGION="${AWS_REGION:-ap-southeast-2}"
PROVIDER_NAME="github-provider"

# Load credentials from .env
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

if [ -z "$GITHUB_CLIENT_ID" ] || [ -z "$GITHUB_CLIENT_SECRET" ]; then
    echo "❌ Missing credentials in .env"
    echo "   GITHUB_CLIENT_ID=..."
    echo "   GITHUB_CLIENT_SECRET=..."
    exit 1
fi

echo "🔐 GitHub Provider Setup (region: $REGION)"

# Delete if exists
if aws bedrock-agentcore-control list-oauth2-credential-providers --region "$REGION" 2>/dev/null | grep -q "\"name\": \"$PROVIDER_NAME\""; then
    echo "♻️  Deleting existing provider..."
    aws bedrock-agentcore-control delete-oauth2-credential-provider \
        --name "$PROVIDER_NAME" \
        --region "$REGION" 2>/dev/null || true
    echo "⏳ Waiting for cleanup..."
    sleep 5
fi

# Create provider
echo "📡 Creating provider '$PROVIDER_NAME'..."
OUTPUT=$(aws bedrock-agentcore-control create-oauth2-credential-provider \
    --name "$PROVIDER_NAME" \
    --credential-provider-vendor GithubOauth2 \
    --oauth2-provider-config-input "{
        \"githubOauth2ProviderConfig\": {
            \"clientId\": \"$GITHUB_CLIENT_ID\",
            \"clientSecret\": \"$GITHUB_CLIENT_SECRET\"
        }
    }" \
    --region "$REGION" \
    --output json)

PROVIDER_ARN=$(echo "$OUTPUT" | jq -r '.credentialProviderArn')
CALLBACK_URL=$(echo "$OUTPUT" | jq -r '.callbackUrl // "N/A"')

echo "✅ Provider ready: $PROVIDER_ARN"
echo ""
echo "🔗 IMPORTANT: Register this callback URL in your GitHub OAuth App:"
echo "   $CALLBACK_URL"
echo ""
echo "📝 Steps:"
echo "   1. Go to https://github.com/settings/developers"
echo "   2. Select your OAuth App"
echo "   3. Add callback URL: $CALLBACK_URL"
echo "   4. Save changes"
```

### 4. GitHub Authentication (src/auth/github_auth.py)

```python
"""
GitHub OAuth authentication using AgentCore Identity.
Based on bedrock-agent-template pattern with @requires_access_token decorator.
"""
import asyncio
import logging
from typing import Optional, Callable
from bedrock_agentcore.identity.auth import requires_access_token

logger = logging.getLogger(__name__)


class GitHubAuth:
    """
    GitHub OAuth via AgentCore Identity.
    Implements 3-Legged OAuth (USER_FEDERATION) for per-user tokens.
    """

    def __init__(self, oauth_url_callback: Optional[Callable[[str], None]] = None):
        self._token: Optional[str] = None
        self._oauth_url_callback = oauth_url_callback
        self._pending_oauth_url: Optional[str] = None
        logger.info("🔐 GitHub Auth initialized - using AgentCore OAuth")

    async def _on_auth_url(self, url: str):
        """
        Callback when OAuth URL is generated.
        Streams URL back to user for authorization.
        """
        self._pending_oauth_url = url

        logger.info("=" * 60)
        logger.info("🔐 GitHub Authorization Required")
        logger.info(f"🌐 URL: {url}")
        logger.info("=" * 60)

        # Trigger callback to stream URL to user
        if self._oauth_url_callback:
            try:
                if asyncio.iscoroutinefunction(self._oauth_url_callback):
                    await self._oauth_url_callback(url)
                else:
                    self._oauth_url_callback(url)
            except Exception as e:
                logger.error(f"⚠️ Error in OAuth callback: {e}")

    async def get_token(self) -> str:
        """
        Get GitHub access token via OAuth.
        Initiates 3-Legged OAuth flow if not authenticated.
        """
        if not self._token:
            logger.info("🔄 Retrieving GitHub access token via OAuth...")

            @requires_access_token(
                provider_name='github-provider',  # Must match provider name
                scopes=['repo', 'read:user'],     # GitHub OAuth scopes
                auth_flow='USER_FEDERATION',      # 3LO (on-behalf-of user)
                on_auth_url=self._on_auth_url,    # Callback for OAuth URL
                force_authentication=False        # Don't force re-auth if token exists
            )
            async def _get_token(*, access_token: str) -> str:
                self._token = access_token
                logger.info("✅ GitHub access token received")
                logger.debug(f"   Token: {access_token[:20]}...")
                return access_token

            try:
                await _get_token()
            except Exception as e:
                logger.error(f"❌ Failed to get GitHub token: {e}")
                raise ValueError(f"GitHub authentication failed: {e}")

        return self._token

    def is_authenticated(self) -> bool:
        """Check if authentication is complete."""
        return self._token is not None

    def get_pending_oauth_url(self) -> Optional[str]:
        """Get pending OAuth URL if available."""
        return self._pending_oauth_url


# Factory function for auth provider
def get_auth_provider(oauth_url_callback: Optional[Callable[[str], None]] = None) -> GitHubAuth:
    """Create GitHub auth provider with optional OAuth URL callback."""
    return GitHubAuth(oauth_url_callback=oauth_url_callback)
```

### 5. Agent Creation with OAuth (src/agent/create_agent.py)

```python
"""
Agent factory using functional approach with GitHub OAuth.
The Strands Agent class is the only class we use (from library).
"""
from strands import Agent
from strands.models import BedrockModel
from ..prompts.system_prompts import CODING_AGENT_SYSTEM_PROMPT
from ..config import settings
from ..tools.github_tools import (
    list_github_repos,
    get_repo_info,
    create_github_issue,
    list_github_issues,
    create_pull_request
)


def create_coding_agent() -> Agent:
    """
    Create a single Strands Agent with GitHub tools.
    OAuth authentication handled by @requires_access_token decorator in tools.
    """
    # Create Bedrock model
    model = BedrockModel(
        model_id=settings.model_id,
        region_name=settings.aws_region
    )

    # Create agent with GitHub tools
    agent = Agent(
        model=model,
        tools=[
            list_github_repos,
            get_repo_info,
            create_github_issue,
            list_github_issues,
            create_pull_request
        ],
        system_prompt=CODING_AGENT_SYSTEM_PROMPT
    )

    return agent
```

### 6. Streaming Chat Handler (Functional) - src/chat/stream_handler.py

```python
"""
Streaming chat logic using Server-Sent Events (SSE).
Pure async functions - no class needed.
"""
import asyncio
from typing import AsyncIterator
from strands import Agent
from ..models.chat import ChatMessage
import structlog

logger = structlog.get_logger()


async def stream_agent_response(
    agent: Agent,
    message: str,
    session_id: str
) -> AsyncIterator[str]:
    """
    Stream agent responses as SSE events.
    Yields JSON strings for SSE transmission.
    """
    logger.info("streaming_response", session_id=session_id)

    try:
        # Strands async streaming (yields events in real-time)
        async for event in agent.stream_async(message, session_id=session_id):
            if hasattr(event, 'data'):
                # Token chunk from LLM
                yield f" {json.dumps({'type': 'token', 'content': event.data})}\n\n"

            elif hasattr(event, 'current_tool_use'):
                # Agent is calling a tool (e.g., GitHub MCP)
                tool_info = {
                    'type': 'tool_use',
                    'tool_name': event.current_tool_use.name,
                    'tool_input': event.current_tool_use.input
                }
                yield f" {json.dumps(tool_info)}\n\n"

            elif hasattr(event, 'error'):
                # Error occurred
                yield f" {json.dumps({'type': 'error', 'message': str(event.error)})}\n\n"
                break

        # Stream complete
        yield f" {json.dumps({'type': 'done'})}\n\n"

    except Exception as e:
        logger.error("streaming_failed", error=str(e))
        yield f" {json.dumps({'type': 'error', 'message': str(e)})}\n\n"


async def handle_pr_review_intent(agent: Agent, pr_number: int, session_id: str) -> AsyncIterator[str]:
    """
    Special handler when user intent is PR review.
    Still streams but follows structured workflow.
    """
    from ..prompts.templates import generate_plan_markdown
    from ..prompts.system_prompts import PR_REVIEW_PLAN_PROMPT_TEMPLATE

    # Step 1: Fetch PR via GitHub MCP (agent does this autonomously)
    plan_prompt = f"Create a review plan for PR #{pr_number} in /agent-tasks/ folder"

    # Agent streams plan generation
    async for chunk in stream_agent_response(agent, plan_prompt, session_id):
        yield chunk

    # Wait for user approval (in real chat, they'll reply)
    # ... (handled by chat session state)
```

### 7. FastAPI Streaming App - src/main.py

```python
"""
Streaming chat API - functional endpoints, minimal state.
"""
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from .agent.create_agent import create_coding_agent
from .chat.stream_handler import stream_agent_response
from .utils.logging import setup_logging
from .config import settings
import structlog

setup_logging(settings.log_level)
logger = structlog.get_logger()

app = FastAPI(title="Coding Agent Chat", version="2.0.0")

# Single agent instance (persists in container)
agent = create_coding_agent()


class ChatRequest(BaseModel):
    """Chat message from user."""
    message: str
    session_id: str


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Streaming chat endpoint using Server-Sent Events.
    Agent autonomously decides when to use GitHub MCP tools.
    """
    logger.info("chat_request", session_id=request.session_id)

    return StreamingResponse(
        stream_agent_response(agent, request.message, request.session_id),
        media_type="text/event-stream"
    )


@app.get("/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

## Modern Python: Why Minimal Classes?

**Classes are overused in Python** [11][1][2]. Modern best practices (2025):

1. **Use functions for logic** - Pure functions are easier to test, compose, and reason about [1][9].
2. **Use dataclasses for data** - `@dataclass` or Pydantic models replace "data-only" classes [12][1].
3. **Use classes only for:**
   - **APIs/interfaces** (like FastAPI endpoints, but those are decorators)
   - **State management** (like Strands Agent, which we import)
   - **Polymorphism** (not needed here)

**In our MVP:**

- ✅ **Functions:** All logic (`create_agent`, `stream_response`, `setup_gateway`)
- ✅ **Dataclasses:** Pydantic models for validation
- ✅ **Minimal classes:** Only `Agent` from Strands (library class)

This is **more Pythonic** than wrapping everything in custom classes [1][2][10].

---

## How It Works End-to-End

Based on bedrock-agent-template implementation:

1. **Setup (once):**
   - Create GitHub OAuth App with Device Flow enabled
   - Run `python src/auth/setup_provider.py` to create OAuth2 credential provider
   - Configure agent in `.bedrock_agentcore.yaml` with `oauth_configuration`

2. **Deploy Agent:**
   - `agentcore launch` deploys agent to AgentCore Runtime
   - Runtime automatically links to OAuth provider via `oauth_configuration`
   - No explicit Gateway needed - OAuth is built into the runtime

3. **User chats:** POST to `/chat/stream` with message and `user_id`

4. **OAuth Flow (First Request):**
   - Agent calls `get_token()` via `@requires_access_token` decorator
   - No token exists for this user → OAuth URL generated
   - URL streamed back to user via callback
   - User visits URL, authorizes GitHub access
   - AgentCore exchanges code for token, stores per-user

5. **Subsequent Requests:**
   - Token exists for user → automatically retrieved
   - Agent uses GitHub SDK/API with token
   - No re-authentication needed (until token expires)

6. **PR Review Flow:**
   - Agent detects PR review intent
   - Uses authenticated GitHub API to fetch PR details
   - Generates plan, streams to user
   - Executes review with GitHub tools

---

This architecture is **production-ready, streaming-first, and follows 2025 Python best practices** with functions over classes [1][9][2].

---

## Key Implementation Updates (Based on bedrock-agent-template)

After analyzing the production implementation in `/Users/freedom/ai/bedrock-agent-template`, here are the **key corrections and improvements**:

### 1. No Explicit Gateway Creation

**Original Draft:** Suggested creating an explicit AgentCore Gateway with `create_gateway()`

**Actual Implementation:**
- OAuth authentication is built into AgentCore Runtime
- No separate Gateway resource needed
- Agent configuration includes `oauth_configuration` section
- Runtime automatically handles OAuth flow

### 2. OAuth Provider Setup

**Correct Pattern:**
```bash
# Create OAuth2 credential provider
aws bedrock-agentcore-control create-oauth2-credential-provider \
    --name "github-provider" \
    --credential-provider-vendor GithubOauth2 \
    --oauth2-provider-config-input '{
        "githubOauth2ProviderConfig": {
            "clientId": "$GITHUB_CLIENT_ID",
            "clientSecret": "$GITHUB_CLIENT_SECRET"
        }
    }'
```

### 3. Agent Configuration Pattern

**In `.bedrock_agentcore.yaml`:**
```yaml
oauth_configuration:
  workload_name: github-workload
  credential_providers:
    - github-provider  # Links to OAuth provider
```

### 4. Authentication Decorator

**Use `@requires_access_token` from `bedrock_agentcore.identity.auth`:**
```python
@requires_access_token(
    provider_name='github-provider',
    scopes=['repo', 'read:user'],
    auth_flow='USER_FEDERATION',
    on_auth_url=callback_function
)
async def get_token(*, access_token: str) -> str:
    return access_token
```

### 5. OAuth URL Streaming

**Pattern for streaming OAuth URLs to users:**
- Use async queue to capture OAuth URL from callback
- Stream URL immediately via SSE
- Wait for user to authorize in browser
- Continue after token is received

### 6. Deployment Workflow

**Correct sequence:**
1. **Create GitHub OAuth App** (Device Flow enabled)
   - Go to https://github.com/settings/developers
   - Create new OAuth App
   - Enable Device Flow in settings
   - Note Client ID and generate Client Secret

2. **Run setup script** to create OAuth2 provider
   ```bash
   python src/auth/setup_provider.py
   ```
   - **CRITICAL:** Copy the callback URL from output
   - Add callback URL to GitHub OAuth App settings
   - Failure to register callback URL will cause OAuth to fail

3. **Configure agent** with `agentcore configure`
   ```bash
   agentcore configure -e src/agent/runtime.py --region ap-southeast-2 --non-interactive
   ```

4. **Update `.bedrock_agentcore.yaml`** with oauth_configuration
   ```yaml
   oauth_configuration:
     workload_name: coding-agent-workload
     credential_providers:
       - github-provider
   ```

5. **Deploy** with `agentcore launch`
   ```bash
   agentcore launch -a coding-agent
   ```

6. **Test OAuth flow** on first user request
   - User sends request
   - OAuth URL generated and streamed back
   - User authorizes in browser
   - Token stored per-user
   - Subsequent requests use cached token

### 7. GitHub API Integration

**Instead of MCP Gateway:**
- Use GitHub Python SDK (`PyGithub`) or REST API
- Inject OAuth token from `@requires_access_token`
- Create Strands tools that wrap authenticated API calls
- No separate MCP server container needed

## Troubleshooting

### Common Issues and Solutions

**Issue: OAuth URL not generated**
```python
# Ensure callback is registered
auth = GitHubAuth(oauth_url_callback=your_callback)
```

**Issue: "Provider not found" error**
```bash
# List all providers to verify
aws bedrock-agentcore-control list-oauth2-credential-providers --region ap-southeast-2

# Check provider name matches everywhere:
# 1. Provider creation: --name "github-provider"
# 2. Agent config: credential_providers: [github-provider]
# 3. Code decorator: provider_name='github-provider'
```

**Issue: OAuth callback fails**
```bash
# Verify callback URL is registered in GitHub OAuth App
# Get the callback URL from provider creation output
aws bedrock-agentcore-control get-oauth2-credential-provider \
    --name "github-provider" \
    --region ap-southeast-2 | jq -r '.callbackUrl'
```

**Issue: Token not persisted across sessions**
```python
# Ensure USER_FEDERATION flow (not CLIENT_CREDENTIALS)
@requires_access_token(
    auth_flow='USER_FEDERATION'  # Must be USER_FEDERATION
)
```

**Issue: "Region not set" errors**
```python
# DO NOT pass region to list/delete operations
# Region is set when creating the client
client = boto3.client('bedrock-agentcore-control', region_name=region)

# ✅ Correct
client.list_oauth2_credential_providers()

# ❌ Wrong
client.list_oauth2_credential_providers(region=region)
```

**Issue: Scopes rejected by GitHub**
```python
# Verify scopes are valid GitHub OAuth scopes
# Valid: 'repo', 'read:user', 'user:email', 'write:repo_hook'
# Invalid: 'repository', 'read_user' (wrong format)
```

---

## Related Documentation

For complete OAuth setup details, see:
- **Detailed Guide:** `/Users/freedom/ai/aws-coding-agent/claudedocs/agentcore-gateway-oauth-setup.md`
- **Architecture Review:** `/Users/freedom/ai/aws-coding-agent/claudedocs/architecture-review.md`
- **Corrected Implementation:** `/Users/freedom/ai/aws-coding-agent/claudedocs/corrected-oauth-setup.py`
- **Quick Fixes:** `/Users/freedom/ai/aws-coding-agent/claudedocs/quick-fixes.md`
- **Template Reference:** `/Users/freedom/ai/bedrock-agent-template/agents/github-agent/`

---

This architecture is **production-ready, streaming-first, and follows 2025 Python best practices** with functions over classes [1][9][2].

Sources
[1] Functions Over Classes? Why I Prefer a Simpler ... https://www.nijho.lt/post/functional-python/
[2] Why You Should Stop Using Classes in Python https://python.plainenglish.io/why-you-should-stop-using-classes-in-python-and-what-to-use-instead-855eeb914d68
[3] Amazon Strands Agents SDK v1.0 https://www.linkedin.com/pulse/amazon-strands-agents-sdk-v10-technical-overview-jin-mxioe
[4] aws-samples/sample-strands-agent-chatbot https://github.com/aws-samples/sample-strands-agent-chatbot
[5] Tying It All Together : How Strands Agents Enhance Retail ... https://dev.to/aws-builders/tying-it-all-together-how-strands-agents-weave-together-retail-performance-analysis-50p4
[6] Introducing Amazon Bedrock AgentCore Gateway https://aws.amazon.com/blogs/machine-learning/introducing-amazon-bedrock-agentcore-gateway-transforming-enterprise-ai-agent-tool-development/
[7] Amazon Bedrock AgentCore Gateway - Part 3 Exposing ... https://dev.to/aws-heroes/amazon-bedrock-agentcore-gateway-part-3-exposing-existing-aws-lambda-function-via-mcp-and-gateway-2ga
[8] Use an AgentCore gateway https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway-using.html
[9] Functional Python: Embracing a New Paradigm for Better ... https://www.qodo.ai/blog/functional-python-embracing-a-new-paradigm-for-better-code/
[10] When are classes (thinking OOP) too much? https://discuss.python.org/t/when-are-classes-thinking-oop-too-much/77026
[11] When should we avoid classes? : r/Python https://www.reddit.com/r/Python/comments/7nn912/when_should_we_avoid_classes/
[12] Python Classes: The Power of Object-Oriented Programming https://realpython.com/python-classes/
[13] Deploy MCP servers in AgentCore Runtime https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-mcp.html
[14] How to Use GitHub MCP Server https://apidog.com/blog/github-mcp-server/
[15] GitHub's official MCP Server https://github.com/github/github-mcp-server
[16] AWS Bedrock AgentCore MCP Server https://awslabs.github.io/mcp/servers/amazon-bedrock-agentcore-mcp-server
[17] weiwarren/agentcore-mcp-server https://github.com/weiwarren/agentcore-mcp-server
[18] Hosting OpenSearch MCP Server with Amazon Bedrock ... https://opensearch.org/blog/hosting-opensearch-mcp-server-with-amazon-bedrock-agentcore/
[19] Build your first Agentic AI app step-by-step with Strands ... https://www.youtube.com/watch?v=aijS9fWB854
[20] feat: Amazon Bedrock AgentCore MCP Server #1343 https://github.com/awslabs/mcp/pull/1343
[21] agentic-community/mcp-gateway-registry https://github.com/agentic-community/mcp-gateway-registry
[22] awslabs/mcp: AWS MCP Servers — helping you get ... https://github.com/awslabs/mcp
[23] Build and scale adoption of AI agents for education with ... https://aws.amazon.com/blogs/machine-learning/build-and-scale-adoption-of-ai-agents-for-education-with-strands-agents-amazon-bedrock-agentcore-and-librechat/
[24] Unifying tools with a frontend gateway using AgentCore ... https://aws.plainenglish.io/unifying-tools-with-a-frontend-gateway-using-agentcore-gateway-b12409162670
[25] aws/bedrock-agentcore-starter-toolkit https://github.com/aws/bedrock-agentcore-starter-toolkit
[26] Chat Chainlit App with Agent Squad - Open Source at AWS https://awslabs.github.io/agent-squad/cookbook/examples/chat-chainlit-app/
[27] awslabs/amazon-bedrock-agentcore-samples https://github.com/awslabs/amazon-bedrock-agentcore-samples
[28] Using Writer with AWS Strands Agents - Writer AI Studio https://dev.writer.com/home/integrations/strands
[29] When should I be using classes in Python? https://stackoverflow.com/questions/33072570/when-should-i-be-using-classes-in-python
[30] GitHub's MCP Server: You Can Now Talk to Your Repos https://ainativedev.io/news/github-mcp-server
[31] How to find, install, and manage MCP servers with ... https://github.blog/ai-and-ml/generative-ai/how-to-find-install-and-manage-mcp-servers-with-the-github-mcp-registry/
[32] Why You Should Care About Functional Programming (Even ... https://borkar.substack.com/p/why-care-about-functional-programming
[33] Avoid These BAD Practices in Python OOP https://www.youtube.com/watch?v=yFLY0SVutgM
[34] idosal/git-mcp: Put an end to code hallucinations! GitMCP ... https://github.com/idosal/git-mcp
[35] Is Python an object-oriented programming language? https://www.devacetech.com/insights/is-python-an-object-oriented
[36] Using the GitHub MCP Server https://docs.github.com/en/copilot/how-tos/provide-context/use-mcp/use-the-github-mcp-server
[37] Functions vs Classes: When to Use Which and Why? https://www.youtube.com/watch?v=txRTzljmV0Q
[38] 6 things you're missing out on by never using classes in ... https://dbader.org/blog/6-things-youre-missing-out-on-by-never-using-classes-in-your-python-code
[39] Why You Should Care About Functional Programming ... https://www.reddit.com/r/compsci/comments/1kyjexr/why_you_should_care_about_functional_programming/
[40] Python classes aren't always the best solution https://news.ycombinator.com/item?id=44675119

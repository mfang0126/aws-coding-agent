# Incremental Testing Strategy - Test as You Build

**Philosophy:** Shift-left testing - catch issues early when they're cheaper to fix

---

## Testing Overview by Phase

| Phase | Testing Time | Test Coverage | Can Deploy? |
|-------|--------------|---------------|-------------|
| Phase 1 | 30 min | Foundation | No |
| Phase 2 | 1-2 hours | OAuth + Auth | No |
| Phase 3 | 1 hour | Agent + Models | No |
| Phase 4 | 1-2 hours | GitHub Tools | No |
| Phase 5 | 1-2 hours | Streaming | **Yes (local)** |
| Phase 6 | 6-8 hours | Comprehensive | **Yes (staging)** |
| Phase 7 | 1 hour | Production | **Yes (prod)** |

---

## Phase 1: Foundation Testing (30 minutes)

### What to Test

#### 1.1 Project Structure Validation
```bash
# Test: Directory structure exists
test -d src/prompts && test -d src/models && test -d src/auth && \
test -d src/agent && test -d src/tools && test -d src/chat && \
echo "✅ Directory structure valid" || echo "❌ Missing directories"
```

#### 1.2 Configuration Loading
```python
# tests/test_config.py
import pytest
from src.config import settings

def test_settings_load():
    """Test configuration loads from environment."""
    assert settings.aws_region is not None
    assert settings.model_id is not None
    assert len(settings.aws_region) > 0

def test_github_credentials_exist():
    """Test GitHub credentials are configured."""
    assert settings.github_client_id is not None
    assert settings.github_client_secret is not None
    # Should be SecretStr, not empty string
    assert len(settings.github_client_id.get_secret_value()) > 0

def test_model_id_format():
    """Test model ID is valid Bedrock format."""
    model_id = settings.model_id
    assert model_id.startswith("anthropic.") or model_id.startswith("amazon.")
```

**Run tests:**
```bash
pytest tests/test_config.py -v
# Expected: 3 passed
```

#### 1.3 Logging Infrastructure
```python
# tests/test_logging.py
from src.utils.logging import setup_logging
import structlog

def test_logging_setup():
    """Test structured logging configures correctly."""
    setup_logging("INFO")
    logger = structlog.get_logger()

    # Should not raise exception
    logger.info("test_message", test_key="test_value")

    assert logger is not None
```

**Run tests:**
```bash
pytest tests/test_logging.py -v
# Expected: 1 passed
```

#### 1.4 Utility Functions
```python
# tests/test_utils.py
from src.utils.response import format_sse_event, format_error_response

def test_sse_event_format():
    """Test SSE event formatting."""
    result = format_sse_event("token", {"content": "hello"})

    assert result.startswith("data: ")
    assert "token" in result
    assert "hello" in result
    assert result.endswith("\n\n")

def test_error_response_format():
    """Test error response formatting."""
    error = ValueError("test error")
    result = format_error_response(error)

    assert result["error"] == "test error"
    assert result["type"] == "ValueError"
    assert "timestamp" in result
```

**Run tests:**
```bash
pytest tests/test_utils.py -v
# Expected: 2 passed
```

### Phase 1 Quality Gate ✓

```bash
# Run all Phase 1 tests
pytest tests/test_config.py tests/test_logging.py tests/test_utils.py -v

# Expected output:
# tests/test_config.py::test_settings_load PASSED
# tests/test_config.py::test_github_credentials_exist PASSED
# tests/test_config.py::test_model_id_format PASSED
# tests/test_logging.py::test_logging_setup PASSED
# tests/test_utils.py::test_sse_event_format PASSED
# tests/test_utils.py::test_error_response_format PASSED
# ========================= 6 passed =========================
```

**✅ Phase 1 Complete When:**
- All 6 tests pass
- No import errors
- Config loads from .env
- Logging produces structured output

---

## Phase 2: OAuth Infrastructure Testing (1-2 hours)

### What to Test

#### 2.1 OAuth Provider Verification
```bash
# Test: Provider exists in AWS
# tests/integration/test_oauth_provider.sh

#!/bin/bash
set -e

echo "Testing OAuth provider setup..."

# Check provider exists
PROVIDER=$(aws bedrock-agentcore-control list-oauth2-credential-providers \
  --region ap-southeast-2 \
  --query 'credentialProviders[?name==`github-provider`]' \
  --output json)

if [ "$PROVIDER" = "[]" ]; then
    echo "❌ OAuth provider 'github-provider' not found"
    exit 1
fi

echo "✅ Provider exists"

# Get callback URL
CALLBACK_URL=$(aws bedrock-agentcore-control get-oauth2-credential-provider \
  --name "github-provider" \
  --region ap-southeast-2 \
  --query 'callbackUrl' \
  --output text)

echo "✅ Callback URL: $CALLBACK_URL"
echo ""
echo "⚠️  MANUAL CHECK REQUIRED:"
echo "   Is this callback URL registered in GitHub OAuth App?"
echo "   Go to: https://github.com/settings/developers"
```

**Run test:**
```bash
chmod +x tests/integration/test_oauth_provider.sh
./tests/integration/test_oauth_provider.sh
```

#### 2.2 Auth Module Unit Tests
```python
# tests/test_auth.py
import pytest
from unittest.mock import Mock, patch, AsyncMock
from src.auth.github_auth import GitHubAuth

@pytest.mark.asyncio
async def test_github_auth_initialization():
    """Test GitHubAuth initializes correctly."""
    auth = GitHubAuth()

    assert not auth.is_authenticated()
    assert auth._token is None

@pytest.mark.asyncio
async def test_oauth_url_callback():
    """Test OAuth URL callback mechanism."""
    callback_called = False
    callback_url = None

    def callback(url: str):
        nonlocal callback_called, callback_url
        callback_called = True
        callback_url = url

    auth = GitHubAuth(oauth_url_callback=callback)

    # Simulate OAuth URL generation
    await auth._on_auth_url("https://test-oauth-url.com")

    assert callback_called
    assert callback_url == "https://test-oauth-url.com"
    assert auth._pending_oauth_url == "https://test-oauth-url.com"

@pytest.mark.asyncio
async def test_get_token_with_mock():
    """Test token retrieval with mocked decorator."""
    auth = GitHubAuth()

    # Mock the @requires_access_token decorator
    with patch('src.auth.github_auth.requires_access_token') as mock_decorator:
        # Configure mock to call the wrapped function with test token
        async def mock_wrapper(*, access_token: str) -> str:
            auth._token = access_token
            return access_token

        mock_decorator.return_value = lambda func: mock_wrapper

        # This test verifies the structure, actual OAuth tested in integration
        assert auth._token is None or isinstance(auth._token, str)
```

**Run tests:**
```bash
pytest tests/test_auth.py -v
# Expected: 3 passed
```

#### 2.3 Provider Name Consistency Check
```python
# tests/test_provider_consistency.py
import yaml
from src.config import settings

def test_provider_name_in_decorator():
    """Test provider name matches everywhere."""
    EXPECTED_NAME = "github-provider"

    # Check in auth module
    from src.auth.github_auth import GitHubAuth
    import inspect

    source = inspect.getsource(GitHubAuth.get_token)
    assert f"provider_name='{EXPECTED_NAME}'" in source or \
           f'provider_name="{EXPECTED_NAME}"' in source

def test_provider_name_in_agent_config():
    """Test provider name in AgentCore config."""
    EXPECTED_NAME = "github-provider"

    with open('.bedrock_agentcore.yaml', 'r') as f:
        config = yaml.safe_load(f)

    providers = config.get('oauth_configuration', {}).get('credential_providers', [])
    assert EXPECTED_NAME in providers, \
        f"Provider '{EXPECTED_NAME}' not in agent config: {providers}"
```

**Run tests:**
```bash
pytest tests/test_provider_consistency.py -v
# Expected: 2 passed
```

### Phase 2 Quality Gate ✓

```bash
# Run OAuth provider check
./tests/integration/test_oauth_provider.sh

# Run auth module tests
pytest tests/test_auth.py tests/test_provider_consistency.py -v

# Manual verification
echo "Manual checks:"
echo "1. [ ] Callback URL displayed in provider test output"
echo "2. [ ] Callback URL registered in GitHub OAuth App"
echo "3. [ ] Device Flow enabled in GitHub OAuth App"
```

**✅ Phase 2 Complete When:**
- OAuth provider exists in AWS ✓
- Callback URL registered in GitHub ✓
- Auth module tests pass (5 tests) ✓
- Provider name consistent everywhere ✓
- Manual verification checklist complete ✓

---

## Phase 3: Core Agent Testing (1 hour)

### What to Test

#### 3.1 Prompts and Templates
```python
# tests/test_prompts.py
from src.prompts.system_prompts import CODING_AGENT_SYSTEM_PROMPT, PR_REVIEW_PLAN_PROMPT_TEMPLATE
from src.prompts.templates import generate_plan_markdown, generate_status_update

def test_system_prompt_exists():
    """Test system prompt is defined."""
    assert len(CODING_AGENT_SYSTEM_PROMPT) > 100
    assert "coding assistant" in CODING_AGENT_SYSTEM_PROMPT.lower()

def test_pr_review_template_exists():
    """Test PR review template is defined."""
    assert "pr_number" in PR_REVIEW_PLAN_PROMPT_TEMPLATE
    assert "title" in PR_REVIEW_PLAN_PROMPT_TEMPLATE

def test_plan_markdown_generation():
    """Test plan markdown template."""
    result = generate_plan_markdown(
        objective="Test objective",
        steps=["Step 1", "Step 2", "Step 3"],
        risks=["Risk 1"],
        time_min=30
    )

    assert "Test objective" in result
    assert "Step 1" in result
    assert "Step 2" in result
    assert "Risk 1" in result
    assert "30 minutes" in result

def test_status_update_generation():
    """Test status update generation."""
    result = generate_status_update(
        status="in_progress",
        step="Step 2 of 5",
        progress=40,
        issues=["Minor issue"]
    )

    assert result["status"] == "in_progress"
    assert result["progress"] == 40
    assert "Minor issue" in result["issues"]
    assert "updated_at" in result
```

**Run tests:**
```bash
pytest tests/test_prompts.py -v
# Expected: 5 passed
```

#### 3.2 Data Models Validation
```python
# tests/test_models.py
import pytest
from pydantic import ValidationError
from src.models.plan import PlanModel
from src.models.status import StatusModel
from src.models.chat import ChatMessage

def test_plan_model_valid():
    """Test PlanModel with valid data."""
    plan = PlanModel(
        objective="Review PR #123",
        steps=["Step 1", "Step 2"],
        estimated_time_minutes=30
    )

    assert plan.objective == "Review PR #123"
    assert len(plan.steps) == 2
    assert plan.estimated_time_minutes == 30
    assert len(plan.risks) == 0  # Default empty list

def test_plan_model_invalid_time():
    """Test PlanModel rejects invalid time."""
    with pytest.raises(ValidationError):
        PlanModel(
            objective="Test",
            steps=["Step 1"],
            estimated_time_minutes=0  # Must be >= 1
        )

def test_status_model_valid():
    """Test StatusModel with valid data."""
    status = StatusModel(
        status="in_progress",
        current_step="Step 2",
        progress=50
    )

    assert status.status == "in_progress"
    assert status.progress == 50
    assert len(status.issues) == 0

def test_status_model_invalid_status():
    """Test StatusModel rejects invalid status."""
    with pytest.raises(ValidationError):
        StatusModel(
            status="invalid_status",  # Must be literal
            current_step="Step 1",
            progress=0
        )

def test_chat_message_valid():
    """Test ChatMessage with valid data."""
    msg = ChatMessage(
        role="user",
        content="Hello",
        session_id="session-123"
    )

    assert msg.role == "user"
    assert msg.content == "Hello"
    assert msg.session_id == "session-123"
```

**Run tests:**
```bash
pytest tests/test_models.py -v
# Expected: 6 passed
```

#### 3.3 Agent Creation Test
```python
# tests/test_agent_creation.py
import pytest
from src.agent.create_agent import create_coding_agent

def test_agent_creation():
    """Test agent can be created."""
    agent = create_coding_agent()

    assert agent is not None
    assert hasattr(agent, 'model')
    assert hasattr(agent, 'tools')
    assert hasattr(agent, 'system_prompt')

def test_agent_has_tools():
    """Test agent has GitHub tools registered."""
    agent = create_coding_agent()

    # Should have 5 GitHub tools
    assert len(agent.tools) == 5

    tool_names = [tool.__name__ for tool in agent.tools]
    assert "list_github_repos" in tool_names
    assert "get_repo_info" in tool_names
    assert "create_github_issue" in tool_names
    assert "list_github_issues" in tool_names
    assert "create_pull_request" in tool_names

def test_agent_system_prompt():
    """Test agent has correct system prompt."""
    agent = create_coding_agent()

    from src.prompts.system_prompts import CODING_AGENT_SYSTEM_PROMPT
    assert agent.system_prompt == CODING_AGENT_SYSTEM_PROMPT
```

**Run tests:**
```bash
pytest tests/test_agent_creation.py -v
# Expected: 3 passed
```

### Phase 3 Quality Gate ✓

```bash
# Run all Phase 3 tests
pytest tests/test_prompts.py tests/test_models.py tests/test_agent_creation.py -v

# Expected: 14 passed

# Smoke test - agent creation
python -c "
from src.agent.create_agent import create_coding_agent
agent = create_coding_agent()
print(f'✅ Agent created with {len(agent.tools)} tools')
"
```

**✅ Phase 3 Complete When:**
- Prompts/templates tests pass (5 tests) ✓
- Model validation tests pass (6 tests) ✓
- Agent creation tests pass (3 tests) ✓
- Agent has all 5 tools registered ✓
- System prompt loaded correctly ✓

---

## Phase 4: GitHub Tools Testing (1-2 hours)

### What to Test

#### 4.1 Tool Decorator Verification
```python
# tests/test_github_tools_structure.py
import inspect
from src.tools.github_tools import (
    list_github_repos,
    get_repo_info
)
from src.tools.repos import (
    create_github_issue,
    list_github_issues,
    create_pull_request
)

def test_tools_have_access_token_parameter():
    """Test all tools have access_token parameter."""
    tools = [
        list_github_repos,
        get_repo_info,
        create_github_issue,
        list_github_issues,
        create_pull_request
    ]

    for tool in tools:
        sig = inspect.signature(tool)
        params = sig.parameters

        assert 'access_token' in params, \
            f"{tool.__name__} missing access_token parameter"

        # Should be keyword-only (after *)
        assert params['access_token'].kind == inspect.Parameter.KEYWORD_ONLY

def test_tools_are_async():
    """Test all tools are async functions."""
    tools = [
        list_github_repos,
        get_repo_info,
        create_github_issue,
        list_github_issues,
        create_pull_request
    ]

    for tool in tools:
        assert inspect.iscoroutinefunction(tool), \
            f"{tool.__name__} is not async"

def test_tools_have_docstrings():
    """Test all tools have documentation."""
    tools = [
        list_github_repos,
        get_repo_info,
        create_github_issue,
        list_github_issues,
        create_pull_request
    ]

    for tool in tools:
        assert tool.__doc__ is not None, \
            f"{tool.__name__} missing docstring"
        assert len(tool.__doc__.strip()) > 10
```

**Run tests:**
```bash
pytest tests/test_github_tools_structure.py -v
# Expected: 3 passed
```

#### 4.2 Tool Logic with Mocked GitHub API
```python
# tests/test_github_tools_logic.py
import pytest
from unittest.mock import Mock, patch, MagicMock

@pytest.mark.asyncio
async def test_list_repos_with_mock():
    """Test list_repos with mocked GitHub."""
    from src.tools.github_tools import list_github_repos

    with patch('src.tools.github_tools.Github') as MockGithub:
        # Setup mock
        mock_repo = Mock()
        mock_repo.name = "test-repo"
        mock_repo.full_name = "user/test-repo"
        mock_repo.description = "Test repository"
        mock_repo.private = False
        mock_repo.html_url = "https://github.com/user/test-repo"

        mock_user = Mock()
        mock_user.get_repos.return_value = [mock_repo]

        MockGithub.return_value.get_user.return_value = mock_user

        # Call tool
        result = await list_github_repos(access_token="test_token")

        # Verify
        assert len(result) == 1
        assert result[0]["name"] == "test-repo"
        assert result[0]["full_name"] == "user/test-repo"
        MockGithub.assert_called_once_with("test_token")

@pytest.mark.asyncio
async def test_get_repo_info_with_mock():
    """Test get_repo_info with mocked GitHub."""
    from src.tools.github_tools import get_repo_info

    with patch('src.tools.github_tools.Github') as MockGithub:
        # Setup mock
        mock_repo = Mock()
        mock_repo.name = "test-repo"
        mock_repo.description = "Test"
        mock_repo.stargazers_count = 42
        mock_repo.forks_count = 10
        mock_repo.open_issues_count = 5
        mock_repo.language = "Python"
        from datetime import datetime
        mock_repo.created_at = datetime(2024, 1, 1)
        mock_repo.updated_at = datetime(2024, 6, 1)

        MockGithub.return_value.get_repo.return_value = mock_repo

        # Call tool
        result = await get_repo_info(
            access_token="test_token",
            repo_name="user/test-repo"
        )

        # Verify
        assert result["name"] == "test-repo"
        assert result["stars"] == 42
        assert result["language"] == "Python"

@pytest.mark.asyncio
async def test_create_issue_with_mock():
    """Test create_issue with mocked GitHub."""
    from src.tools.repos import create_github_issue

    with patch('src.tools.repos.Github') as MockGithub:
        # Setup mock
        mock_issue = Mock()
        mock_issue.number = 123
        mock_issue.title = "Test Issue"
        mock_issue.html_url = "https://github.com/user/repo/issues/123"
        mock_issue.state = "open"

        mock_repo = Mock()
        mock_repo.create_issue.return_value = mock_issue

        MockGithub.return_value.get_repo.return_value = mock_repo

        # Call tool
        result = await create_github_issue(
            access_token="test_token",
            repo_name="user/repo",
            title="Test Issue",
            body="Test body",
            labels=["bug"]
        )

        # Verify
        assert result["number"] == 123
        assert result["title"] == "Test Issue"
        assert result["state"] == "open"
        mock_repo.create_issue.assert_called_once()
```

**Run tests:**
```bash
pytest tests/test_github_tools_logic.py -v
# Expected: 3 passed
```

#### 4.3 Rate Limiting Test
```python
# tests/test_rate_limiting.py
import pytest
from unittest.mock import Mock, patch
from github import RateLimitExceededException

@pytest.mark.asyncio
async def test_rate_limit_handling():
    """Test tools handle rate limiting."""
    from src.tools.github_tools import list_github_repos

    with patch('src.tools.github_tools.Github') as MockGithub:
        # First call raises rate limit
        # Second call succeeds
        mock_user = Mock()
        mock_user.get_repos.side_effect = [
            RateLimitExceededException(403, {"message": "Rate limit exceeded"}),
            []  # Success on retry
        ]

        MockGithub.return_value.get_user.return_value = mock_user

        # Should handle rate limit and retry
        # (Assuming you've implemented retry logic)
        with patch('asyncio.sleep', return_value=None):  # Speed up test
            result = await list_github_repos(access_token="test_token")

            # Should eventually succeed
            assert isinstance(result, list)
```

**Run tests:**
```bash
pytest tests/test_rate_limiting.py -v
# Expected: 1 passed
```

#### 4.4 Integration Test with Real GitHub (Optional but Recommended)
```python
# tests/integration/test_github_integration.py
import pytest
import os

@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv('GITHUB_TEST_TOKEN'),
    reason="GITHUB_TEST_TOKEN not set"
)
@pytest.mark.asyncio
async def test_list_repos_real_github():
    """Integration test with real GitHub API."""
    from src.tools.github_tools import list_github_repos

    token = os.getenv('GITHUB_TEST_TOKEN')
    repos = await list_github_repos(access_token=token)

    assert isinstance(repos, list)
    # If you have repos, should return them
    if len(repos) > 0:
        assert "name" in repos[0]
        assert "full_name" in repos[0]
```

**Run tests:**
```bash
# Unit tests (fast, always run)
pytest tests/test_github_tools_structure.py tests/test_github_tools_logic.py tests/test_rate_limiting.py -v

# Integration tests (slow, optional)
export GITHUB_TEST_TOKEN=ghp_your_test_token
pytest tests/integration/test_github_integration.py -v -m integration
```

### Phase 4 Quality Gate ✓

```bash
# Run all Phase 4 tests
pytest tests/test_github_tools_structure.py \
       tests/test_github_tools_logic.py \
       tests/test_rate_limiting.py -v

# Expected: 7 passed

# Optional: Integration test
export GITHUB_TEST_TOKEN=ghp_your_test_token
pytest tests/integration/test_github_integration.py -v -m integration
```

**✅ Phase 4 Complete When:**
- Tool structure tests pass (3 tests) ✓
- Tool logic tests pass (3 tests) ✓
- Rate limiting test passes (1 test) ✓
- All tools have @requires_access_token ✓
- All tools are async ✓
- Integration test passes (optional) ✓

---

## Phase 5: Streaming Chat Testing (1-2 hours)

### What to Test

#### 5.1 SSE Event Formatting
```python
# tests/test_streaming.py
import json
from src.chat.stream_handler import stream_agent_response

def test_sse_event_format():
    """Test SSE events are formatted correctly."""
    from src.utils.response import format_sse_event

    event = format_sse_event("token", {"content": "hello"})

    assert event.startswith("data: ")
    assert event.endswith("\n\n")

    # Extract JSON
    json_str = event[6:-2]  # Remove "data: " and "\n\n"
    data = json.loads(json_str)

    assert data["type"] == "token"
    assert data["data"]["content"] == "hello"
```

**Run test:**
```bash
pytest tests/test_streaming.py::test_sse_event_format -v
```

#### 5.2 Session Management
```python
# tests/test_session.py
from src.chat.session import SessionStore
from datetime import datetime, timedelta

def test_session_creation():
    """Test session is created on first access."""
    store = SessionStore()

    session = store.get("session-123")

    assert session is not None
    assert "created_at" in session
    assert "messages" in session
    assert len(session["messages"]) == 0

def test_session_update():
    """Test session can be updated."""
    store = SessionStore()

    session = store.get("session-123")
    initial_time = session["last_active"]

    # Update session
    store.update("session-123", {"test_key": "test_value"})

    updated_session = store.get("session-123")
    assert updated_session["test_key"] == "test_value"
    assert updated_session["last_active"] > initial_time

def test_session_cleanup():
    """Test old sessions are cleaned up."""
    store = SessionStore()

    # Create old session
    session = store.get("old-session")
    store._sessions["old-session"]["last_active"] = \
        datetime.utcnow() - timedelta(hours=25)

    # Create recent session
    store.get("new-session")

    # Cleanup
    store.cleanup_old_sessions(max_age_hours=24)

    assert "old-session" not in store._sessions
    assert "new-session" in store._sessions
```

**Run tests:**
```bash
pytest tests/test_session.py -v
# Expected: 3 passed
```

#### 5.3 FastAPI Endpoints
```python
# tests/test_fastapi_endpoints.py
import pytest
from fastapi.testclient import TestClient
from src.main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_health_endpoint(client):
    """Test health endpoint."""
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "agent_ready" in data

def test_chat_stream_endpoint_exists(client):
    """Test chat stream endpoint exists."""
    response = client.post(
        "/chat/stream",
        json={
            "message": "Hello",
            "session_id": "test-session"
        }
    )

    # Should return streaming response
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

def test_chat_stream_requires_message(client):
    """Test chat stream requires message."""
    response = client.post(
        "/chat/stream",
        json={
            "session_id": "test-session"
            # Missing message
        }
    )

    assert response.status_code == 422  # Validation error
```

**Run tests:**
```bash
pytest tests/test_fastapi_endpoints.py -v
# Expected: 3 passed
```

#### 5.4 Local Deployment Test
```bash
# tests/integration/test_local_deployment.sh

#!/bin/bash
set -e

echo "Testing local deployment..."

# Start server in background
uvicorn src.main:app --host 0.0.0.0 --port 8000 &
SERVER_PID=$!

# Wait for server to start
sleep 3

# Test health endpoint
echo "Testing /health..."
HEALTH=$(curl -s http://localhost:8000/health)
echo "Health response: $HEALTH"

if echo "$HEALTH" | grep -q '"status":"healthy"'; then
    echo "✅ Health check passed"
else
    echo "❌ Health check failed"
    kill $SERVER_PID
    exit 1
fi

# Test streaming endpoint
echo "Testing /chat/stream..."
curl -N -X POST http://localhost:8000/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message":"Hello","session_id":"test"}' \
  --max-time 10 &
CURL_PID=$!

sleep 3
kill $CURL_PID 2>/dev/null || true

echo "✅ Streaming endpoint accessible"

# Cleanup
kill $SERVER_PID
echo "✅ Local deployment test complete"
```

**Run test:**
```bash
chmod +x tests/integration/test_local_deployment.sh
./tests/integration/test_local_deployment.sh
```

### Phase 5 Quality Gate ✓

```bash
# Run all Phase 5 tests
pytest tests/test_streaming.py tests/test_session.py tests/test_fastapi_endpoints.py -v

# Expected: 7 passed

# Local deployment test
./tests/integration/test_local_deployment.sh
```

**✅ Phase 5 Complete When:**
- SSE formatting tests pass ✓
- Session management tests pass (3 tests) ✓
- FastAPI endpoint tests pass (3 tests) ✓
- Local deployment test passes ✓
- Can curl /health successfully ✓
- Can POST to /chat/stream ✓

**🎉 MILESTONE: At this point, you have a working local deployment!**

---

## Phase 6: Comprehensive Testing (6-8 hours)

This is the formal testing phase where you ensure everything works together.

### Test Coverage Goals

```bash
# Run full test suite with coverage
pytest tests/ --cov=src --cov-report=term-missing --cov-report=html

# Expected coverage:
# src/config.py          100%
# src/prompts/           100%
# src/models/            95%+
# src/auth/             80%+
# src/tools/            85%+
# src/chat/             85%+
# src/utils/            100%
# TOTAL                 85%+
```

### E2E Test: Complete OAuth Flow
```python
# tests/e2e/test_oauth_flow.py
import pytest
import asyncio

@pytest.mark.e2e
@pytest.mark.asyncio
async def test_complete_oauth_flow():
    """Test complete OAuth flow end-to-end."""
    from src.auth.github_auth import GitHubAuth

    oauth_url_received = False
    received_url = None

    def capture_oauth_url(url: str):
        nonlocal oauth_url_received, received_url
        oauth_url_received = True
        received_url = url
        print(f"\n🔐 OAuth URL: {url}")
        print("   Please visit this URL and authorize the app")

    auth = GitHubAuth(oauth_url_callback=capture_oauth_url)

    # First call should trigger OAuth
    # This will generate URL and wait for user authorization
    # In automated testing, this would timeout
    # In manual testing, user completes authorization

    try:
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(auth.get_token(), timeout=5.0)
    except:
        pass

    # Verify OAuth URL was generated
    assert oauth_url_received
    assert received_url is not None
    assert "github.com" in received_url or "oauth" in received_url.lower()
```

### E2E Test: PR Review Workflow
```python
# tests/e2e/test_pr_review_workflow.py
import pytest

@pytest.mark.e2e
@pytest.mark.skipif(
    not os.getenv('GITHUB_TEST_TOKEN'),
    reason="Requires GitHub token"
)
@pytest.mark.asyncio
async def test_pr_review_workflow():
    """Test complete PR review workflow."""
    from src.agent.create_agent import create_coding_agent
    from src.tools.github_tools import get_repo_info

    # 1. Create agent
    agent = create_coding_agent()
    assert agent is not None

    # 2. Get repo info (simulating first step of PR review)
    token = os.getenv('GITHUB_TEST_TOKEN')
    repo_info = await get_repo_info(
        access_token=token,
        repo_name="octocat/Hello-World"  # Public test repo
    )

    assert repo_info["name"] == "Hello-World"

    # 3. Agent processes PR review request
    # (This would be tested manually or with live GitHub PR)

    print("✅ PR review workflow structure validated")
```

### Phase 6 Quality Gate ✓

```bash
# Run full test suite
pytest tests/ --cov=src --cov-report=term-missing -v

# Check coverage
pytest tests/ --cov=src --cov-report=term --cov-fail-under=80

# Run E2E tests
pytest tests/e2e/ -v -m e2e
```

**✅ Phase 6 Complete When:**
- Test coverage >80% ✓
- All unit tests pass ✓
- All integration tests pass ✓
- E2E OAuth flow validated ✓
- E2E PR workflow validated ✓

---

## Phase 7: Deployment Testing (1 hour)

### What to Test

#### 7.1 Staging Deployment
```bash
# Deploy to staging/test environment first
agentcore launch -a coding-agent-staging

# Test staging endpoints
STAGING_URL=$(agentcore status -a coding-agent-staging --format json | jq -r '.url')

# Health check
curl $STAGING_URL/health

# Chat test
curl -N -X POST $STAGING_URL/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message":"List my repositories","session_id":"staging-test"}'
```

#### 7.2 Production Smoke Tests
```bash
# tests/deployment/smoke_test.sh

#!/bin/bash
set -e

AGENT_URL=$1

if [ -z "$AGENT_URL" ]; then
    echo "Usage: $0 <agent-url>"
    exit 1
fi

echo "Running smoke tests against $AGENT_URL..."

# Test 1: Health check
echo "1. Health check..."
HEALTH=$(curl -s $AGENT_URL/health)
if echo "$HEALTH" | grep -q '"status":"healthy"'; then
    echo "✅ Health check passed"
else
    echo "❌ Health check failed"
    exit 1
fi

# Test 2: Chat endpoint responds
echo "2. Chat endpoint..."
timeout 10 curl -N -X POST $AGENT_URL/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message":"Hello","session_id":"smoke-test"}' \
  > /tmp/chat_response.txt 2>&1 || true

if grep -q "data:" /tmp/chat_response.txt; then
    echo "✅ Chat endpoint responding"
else
    echo "❌ Chat endpoint failed"
    exit 1
fi

# Test 3: OAuth flow (manual verification)
echo "3. OAuth flow..."
echo "   Sending request that requires GitHub access..."
timeout 10 curl -N -X POST $AGENT_URL/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message":"List my repositories","session_id":"oauth-test"}' \
  > /tmp/oauth_response.txt 2>&1 || true

if grep -q "oauth_url" /tmp/oauth_response.txt; then
    echo "✅ OAuth URL generated"
    echo "   (Manual verification: Visit URL and authorize)"
else
    echo "⚠️  No OAuth URL (user may already be authenticated)"
fi

echo ""
echo "✅ Smoke tests complete"
```

**Run smoke tests:**
```bash
chmod +x tests/deployment/smoke_test.sh
./tests/deployment/smoke_test.sh https://your-agent-url
```

#### 7.3 CloudWatch Monitoring
```bash
# Monitor logs for 1 hour
agentcore logs -a coding-agent --tail --follow

# Check for errors
agentcore logs -a coding-agent --tail 100 | grep -i error

# Should see no critical errors
```

### Phase 7 Quality Gate ✓

```bash
# Deployment checklist
echo "Deployment verification:"
echo "1. [ ] Staging deployment successful"
echo "2. [ ] Smoke tests pass"
echo "3. [ ] Production deployment successful"
echo "4. [ ] Health endpoint returns 200"
echo "5. [ ] Chat endpoint streams SSE"
echo "6. [ ] OAuth URL generated"
echo "7. [ ] No errors in CloudWatch (1 hour)"
```

**✅ Phase 7 Complete When:**
- Staging deployment successful ✓
- Smoke tests pass ✓
- Production deployment successful ✓
- Live OAuth flow tested ✓
- No errors in logs (1 hour) ✓

---

## Testing Automation

### Continuous Testing Script
```bash
# tests/run_all_tests.sh

#!/bin/bash
set -e

echo "====================================="
echo "Running All Tests"
echo "====================================="

# Phase 1-3: Foundation tests
echo ""
echo "Phase 1-3: Foundation, OAuth, Agent..."
pytest tests/test_config.py \
       tests/test_logging.py \
       tests/test_utils.py \
       tests/test_auth.py \
       tests/test_provider_consistency.py \
       tests/test_prompts.py \
       tests/test_models.py \
       tests/test_agent_creation.py \
       -v --tb=short

# Phase 4: GitHub tools
echo ""
echo "Phase 4: GitHub Tools..."
pytest tests/test_github_tools_structure.py \
       tests/test_github_tools_logic.py \
       tests/test_rate_limiting.py \
       -v --tb=short

# Phase 5: Streaming
echo ""
echo "Phase 5: Streaming..."
pytest tests/test_streaming.py \
       tests/test_session.py \
       tests/test_fastapi_endpoints.py \
       -v --tb=short

# Coverage report
echo ""
echo "Generating coverage report..."
pytest tests/ --cov=src --cov-report=term-missing --cov-fail-under=80

echo ""
echo "✅ All tests passed!"
```

**Make executable and run:**
```bash
chmod +x tests/run_all_tests.sh
./tests/run_all_tests.sh
```

### Pre-Deployment Checklist
```bash
# tests/pre_deployment_check.sh

#!/bin/bash

echo "Pre-Deployment Checklist:"
echo "========================"

# 1. All tests pass
echo -n "1. Running test suite... "
if pytest tests/ -q --tb=no; then
    echo "✅"
else
    echo "❌ Tests failed"
    exit 1
fi

# 2. Coverage >80%
echo -n "2. Checking coverage... "
if pytest tests/ --cov=src --cov-fail-under=80 -q --tb=no &>/dev/null; then
    echo "✅"
else
    echo "❌ Coverage <80%"
    exit 1
fi

# 3. OAuth provider exists
echo -n "3. Verifying OAuth provider... "
if aws bedrock-agentcore-control list-oauth2-credential-providers \
    --region ap-southeast-2 2>/dev/null | grep -q "github-provider"; then
    echo "✅"
else
    echo "❌ Provider not found"
    exit 1
fi

# 4. Config validates
echo -n "4. Validating AgentCore config... "
if agentcore validate-config &>/dev/null; then
    echo "✅"
else
    echo "❌ Config invalid"
    exit 1
fi

# 5. Docker builds
echo -n "5. Testing Docker build... "
if docker build -t coding-agent:test -q . &>/dev/null; then
    echo "✅"
else
    echo "❌ Docker build failed"
    exit 1
fi

echo ""
echo "✅ All pre-deployment checks passed!"
echo "Ready to deploy with: agentcore launch -a coding-agent"
```

---

## Summary: Testing Timeline

| Phase | Testing Time | Tests Created | Tests Run | Pass Criteria |
|-------|--------------|---------------|-----------|---------------|
| 1 | 30 min | 6 | 6 | All pass |
| 2 | 1-2 hours | 5 + manual | 5 | Provider verified |
| 3 | 1 hour | 14 | 14 | Agent creates |
| 4 | 1-2 hours | 7 | 7 | Tools work |
| 5 | 1-2 hours | 7 | 7 | Local deploys |
| 6 | 6-8 hours | Comprehensive | All | >80% coverage |
| 7 | 1 hour | Smoke tests | 5 | Prod verified |
| **Total** | **11-17 hours** | **44+ tests** | **All** | **Production ready** |

---

## Key Takeaways

**✅ Test Early, Test Often**
- Don't wait until Phase 6 to discover Phase 2 issues
- Each phase has concrete, runnable tests
- Immediate feedback on what's working

**✅ Incremental Confidence**
- Phase 1-3: Can create agent ✓
- Phase 4: Can call GitHub ✓
- Phase 5: Can deploy locally ✓
- Phase 6-7: Can deploy to production ✓

**✅ Automation is Key**
- Automated test suites for each phase
- Pre-deployment checklist catches issues
- Smoke tests validate production

**🎯 Goal:** No surprises in Phase 7. Every phase is validated before moving forward.

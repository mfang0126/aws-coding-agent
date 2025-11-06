# AgentCore Gateway & OAuth Provider Setup Guide

Based on analysis of `/Users/freedom/ai/bedrock-agent-template`

## Overview

The bedrock-agent-template uses AWS Bedrock AgentCore's built-in OAuth Gateway functionality to handle secure authentication with third-party services like GitHub. Here's how it works:

## Key Components

### 1. OAuth2 Credential Provider (AWS Resource)
### 2. Agent OAuth Configuration (.bedrock_agentcore.yaml)
### 3. Authentication Implementation (Python code)
### 4. Runtime Integration (Streaming OAuth URLs)

---

## 1. Creating OAuth2 Credential Provider

**File:** `agents/github-agent/scripts/setup_github_provider.sh`

### Script Breakdown

```bash
#!/bin/bash
set -e

REGION="${AWS_REGION:-ap-southeast-2}"
PROVIDER_NAME="github-provider"

# Load credentials from .env
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Check required credentials
if [ -z "$GITHUB_CLIENT_ID" ] || [ -z "$GITHUB_CLIENT_SECRET" ]; then
    echo "❌ Missing credentials in .env"
    echo "   GITHUB_CLIENT_ID=..."
    echo "   GITHUB_CLIENT_SECRET=..."
    exit 1
fi

# Delete existing provider (optional cleanup)
if aws bedrock-agentcore-control list-oauth2-credential-providers --region "$REGION" 2>/dev/null | grep -q "\"name\": \"$PROVIDER_NAME\""; then
    echo "♻️  Deleting existing provider..."
    aws bedrock-agentcore-control delete-oauth2-credential-provider \
        --name "$PROVIDER_NAME" \
        --region "$REGION" 2>/dev/null || true
    sleep 5
fi

# Create OAuth2 credential provider
echo "📡 Creating provider '$PROVIDER_NAME'..."
aws bedrock-agentcore-control create-oauth2-credential-provider \
    --name "$PROVIDER_NAME" \
    --credential-provider-vendor GithubOauth2 \
    --oauth2-provider-config-input "{
        \"githubOauth2ProviderConfig\": {
            \"clientId\": \"$GITHUB_CLIENT_ID\",
            \"clientSecret\": \"$GITHUB_CLIENT_SECRET\"
        }
    }" \
    --region "$REGION" \
    --output json | jq -r '.credentialProviderArn' | xargs echo "✅ Provider ready:"
```

### What This Creates

- **Resource Type**: OAuth2 Credential Provider
- **Provider Name**: `github-provider` (must match agent configuration)
- **Vendor**: `GithubOauth2` (predefined vendor type)
- **Credentials**: GitHub OAuth App client ID and secret
- **Output**: Provider ARN for reference

### AWS CLI Command Pattern

```bash
aws bedrock-agentcore-control create-oauth2-credential-provider \
    --name "<PROVIDER_NAME>" \
    --credential-provider-vendor <VENDOR> \
    --oauth2-provider-config-input '<JSON_CONFIG>' \
    --region <REGION>
```

**Available Vendors:**
- `GithubOauth2` - GitHub OAuth 2.0
- `GoogleOauth2` - Google OAuth 2.0
- `MicrosoftOauth2` - Microsoft OAuth 2.0
- Custom OAuth providers

---

## 2. Agent OAuth Configuration

**File:** `agents/github-agent/.bedrock_agentcore.yaml`

### OAuth Configuration Section

```yaml
oauth_configuration:
  workload_name: github-Hn7UKwBMRj  # Auto-generated workload identifier
  credential_providers:
    - github-provider  # Must match provider name from step 1
```

### Complete Agent Configuration Example

```yaml
default_agent: github
agents:
  github:
    name: github
    entrypoint: src/runtime.py
    platform: linux/arm64
    container_runtime: docker

    aws:
      execution_role: arn:aws:iam::ACCOUNT:role/AgentCoreRole
      execution_role_auto_create: false
      account: 'YOUR_ACCOUNT_ID'
      region: ap-southeast-2
      ecr_repository: ACCOUNT.dkr.ecr.REGION.amazonaws.com/repo-name
      network_configuration:
        network_mode: PUBLIC
      protocol_configuration:
        server_protocol: HTTP

    # OAuth configuration - links to credential provider
    oauth_configuration:
      workload_name: runtime-github-workload
      credential_providers:
        - github-provider  # Name from create-oauth2-credential-provider

    # Optional: custom authorizer for additional auth layers
    authorizer_configuration: null

    # Optional: custom request headers
    request_header_configuration: null
```

---

## 3. Authentication Implementation

**File:** `agents/github-agent/src/auth/agentcore.py`

### Using @requires_access_token Decorator

```python
from bedrock_agentcore.identity.auth import requires_access_token

class AgentCoreGitHubAuth:
    """GitHub OAuth via AgentCore Identity."""

    def __init__(self, oauth_url_callback=None):
        self._token = None
        self._oauth_url_callback = oauth_url_callback
        self._pending_oauth_url = None

    async def _on_auth_url(self, url: str):
        """Callback when OAuth URL is generated."""
        self._pending_oauth_url = url

        # Stream URL back to user immediately
        if self._oauth_url_callback:
            if asyncio.iscoroutinefunction(self._oauth_url_callback):
                await self._oauth_url_callback(url)
            else:
                self._oauth_url_callback(url)

    async def get_token(self) -> str:
        """Get GitHub access token via OAuth."""
        if not self._token:
            @requires_access_token(
                provider_name="github-provider",  # Must match provider name
                scopes=["repo", "read:user"],      # GitHub OAuth scopes
                auth_flow="USER_FEDERATION",       # 3-Legged OAuth (on-behalf-of)
                on_auth_url=self._on_auth_url,     # Callback for OAuth URL
                force_authentication=False         # Don't force re-auth if token exists
            )
            async def _oauth_with_callback(*, access_token: str) -> str:
                self._token = access_token
                return access_token

            await _oauth_with_callback()

        return self._token
```

### Key Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `provider_name` | Name of OAuth2 credential provider | `"github-provider"` |
| `scopes` | OAuth scopes to request | `["repo", "read:user"]` |
| `auth_flow` | OAuth flow type | `"USER_FEDERATION"` (3LO) |
| `on_auth_url` | Callback when OAuth URL generated | `async def callback(url: str)` |
| `force_authentication` | Force new auth even if token exists | `False` |

### Auth Flow Types

- **`USER_FEDERATION`**: 3-Legged OAuth (on-behalf-of user)
  - User authenticates via browser
  - Token is user-specific
  - Best for GitHub, Google, Microsoft

- **`CLIENT_CREDENTIALS`**: 2-Legged OAuth (app-to-app)
  - No user interaction
  - Service account credentials
  - Best for backend integrations

---

## 4. Runtime Integration

**File:** `agents/github-agent/src/runtime.py`

### Streaming OAuth URLs to User

```python
@app.entrypoint
async def strands_agent_github(payload):
    """AgentCore Runtime entrypoint with OAuth URL streaming."""

    user_input = payload.get("prompt", "")
    oauth_url_queue = asyncio.Queue()

    # Callback to stream OAuth URL immediately
    def stream_oauth_url_callback(url: str):
        oauth_url_queue.put_nowait(url)
        print(f"📤 OAuth URL queued: {url[:50]}...")

    # Register callback
    auth.oauth_url_callback = stream_oauth_url_callback

    # Monitor for OAuth URL
    async def monitor_oauth_queue():
        try:
            url = await asyncio.wait_for(oauth_url_queue.get(), timeout=2.0)
            oauth_message = create_oauth_message(url)

            return AgentResponse(
                success=False,
                message=oauth_message,
                data={"oauth_url": url, "requires_authorization": True}
            )
        except asyncio.TimeoutError:
            return None  # No OAuth needed

    # Start auth and monitoring concurrently
    auth_task = asyncio.create_task(auth.get_github_access_token())
    oauth_monitor_task = asyncio.create_task(monitor_oauth_queue())

    done, pending = await asyncio.wait(
        [auth_task, oauth_monitor_task],
        return_when=asyncio.FIRST_COMPLETED
    )

    # Check if OAuth URL was received
    if oauth_monitor_task in done:
        oauth_response = await oauth_monitor_task
        if oauth_response:
            # Stream OAuth URL to user
            yield format_client_text(oauth_response.message)
            auth_task.cancel()
            return  # Wait for user to authorize

    # Authentication successful, proceed
    await auth_task
    yield format_client_text("✅ GitHub authentication successful")

    # Process agent request...
    stream = agent.stream_async(user_input)
    async for event in stream:
        yield format_client_text(extract_text_from_event(event))
```

---

## How Gateway is Created

### Important: Gateway is Implicit!

**The gateway is NOT explicitly created** - it's automatically provisioned by AgentCore when you deploy an agent with `oauth_configuration`.

### Deployment Process

1. **Configure Agent with OAuth**
   ```bash
   agentcore configure -e src/runtime.py --region ap-southeast-2
   ```

2. **Deploy Agent**
   ```bash
   agentcore launch -a github
   ```

3. **AgentCore Automatically Creates:**
   - Gateway resource
   - Gateway URL endpoint
   - OAuth authorization endpoint
   - Token exchange mechanism
   - Secure credential storage

### Verification

```bash
# List all gateways (if API available)
aws bedrock-agentcore-control list-gateways --region ap-southeast-2

# Check agent status (includes gateway info)
agentcore status -a github
```

---

## Complete Setup Workflow

### Step 1: Create GitHub OAuth App

1. Go to https://github.com/settings/developers
2. Create new OAuth App
3. Enable **Device Flow** (important!)
4. Note `Client ID` and generate `Client Secret`

### Step 2: Configure Environment

```bash
# .env file
GITHUB_CLIENT_ID=Iv1.abc123...
GITHUB_CLIENT_SECRET=abc123def456...
AWS_REGION=ap-southeast-2
```

### Step 3: Create OAuth2 Credential Provider

```bash
# Run setup script
./agents/github-agent/scripts/setup_github_provider.sh

# Or manually
aws bedrock-agentcore-control create-oauth2-credential-provider \
    --name "github-provider" \
    --credential-provider-vendor GithubOauth2 \
    --oauth2-provider-config-input '{
        "githubOauth2ProviderConfig": {
            "clientId": "'"$GITHUB_CLIENT_ID"'",
            "clientSecret": "'"$GITHUB_CLIENT_SECRET"'"
        }
    }' \
    --region ap-southeast-2
```

### Step 4: Configure Agent

```bash
agentcore configure \
    -e src/runtime.py \
    --region ap-southeast-2 \
    --non-interactive
```

This creates `.bedrock_agentcore.yaml` with oauth_configuration.

### Step 5: Update OAuth Configuration

Edit `.bedrock_agentcore.yaml`:

```yaml
oauth_configuration:
  workload_name: github-workload
  credential_providers:
    - github-provider  # Must match provider name
```

### Step 6: Deploy Agent

```bash
# Build and deploy
agentcore launch -a github

# Check status
agentcore status -a github
```

### Step 7: Test OAuth Flow

```bash
# Invoke agent
agentcore invoke -a github '{"prompt": "list my repos"}' --user-id "alice"

# Expected flow:
# 1. Agent detects no token for user "alice"
# 2. Generates OAuth URL via @requires_access_token
# 3. Streams URL back to user
# 4. User visits URL and authorizes
# 5. AgentCore exchanges code for token
# 6. Agent receives token and completes request
```

---

## Key Concepts

### 1. Provider Name Binding

The provider name **MUST** match across three places:

```bash
# 1. Credential provider creation
aws bedrock-agentcore-control create-oauth2-credential-provider \
    --name "github-provider"  # ← Name here

# 2. Agent configuration (.bedrock_agentcore.yaml)
oauth_configuration:
  credential_providers:
    - github-provider  # ← Must match

# 3. Code decorator
@requires_access_token(
    provider_name="github-provider"  # ← Must match
)
```

### 2. User Federation (3-Legged OAuth)

- Each user gets their own token
- Tokens are scoped to user identity
- User must authorize via browser
- Tokens are automatically refreshed
- Session isolation by `user_id`

### 3. Token Lifecycle

1. **First Request**: No token exists
   - Agent generates OAuth URL
   - Streams URL to user
   - Waits for authorization

2. **Authorization**: User visits URL
   - Authenticates with GitHub
   - Grants permissions (scopes)
   - Redirected to AgentCore callback

3. **Token Exchange**: AgentCore handles
   - Exchanges auth code for access token
   - Securely stores token
   - Associates with user identity

4. **Subsequent Requests**: Token exists
   - Agent retrieves cached token
   - No re-authentication needed
   - Automatic refresh if expired

---

## Comparison with Manual Gateway Setup

### Template Approach (Implicit Gateway)

```yaml
# .bedrock_agentcore.yaml
oauth_configuration:
  workload_name: github-workload
  credential_providers:
    - github-provider
```

**Pros:**
- ✅ Simple configuration
- ✅ Automatic gateway provisioning
- ✅ Integrated with agent runtime
- ✅ Managed token lifecycle
- ✅ Built-in security

**Cons:**
- ⚠️ Less control over gateway settings
- ⚠️ Tied to agent lifecycle

### Manual Gateway Setup (Explicit)

```bash
# Create gateway explicitly
aws bedrock-agentcore-control create-gateway \
    --name "my-gateway" \
    --protocol-type MCP \
    --role-arn "arn:aws:iam::123456789012:role/GatewayRole"

# Add OAuth target
aws bedrock-agentcore-control create-gateway-target \
    --gateway-identifier "gw-123" \
    --name "github-target" \
    --credential-provider-configurations '[{
        "credentialProviderType": "OAUTH2",
        "credentialProvider": {
            "oauth2CredentialProvider": {
                "providerArn": "arn:aws:bedrock-agentcore:region:account:provider/github-provider"
            }
        }
    }]'
```

**Pros:**
- ✅ Fine-grained control
- ✅ Reusable across agents
- ✅ Can add multiple targets
- ✅ Independent lifecycle

**Cons:**
- ⚠️ More complex setup
- ⚠️ Manual gateway management
- ⚠️ Additional configuration required

---

## Best Practices

### Security

1. **Never commit credentials**
   - Use `.env` for local development
   - Use AWS Secrets Manager for production
   - Add `.env` to `.gitignore`

2. **Minimal scopes**
   ```python
   scopes=["repo", "read:user"]  # Only what you need
   ```

3. **Session isolation**
   ```python
   # Always pass user_id for proper token scoping
   agentcore invoke -a github '{"prompt": "..."}' --user-id "alice"
   ```

### Error Handling

```python
try:
    token = await auth.get_token()
except ValueError as e:
    # Handle OAuth failure
    if auth.get_pending_oauth_url():
        # Stream URL to user
        yield format_client_text(f"🔐 Please authorize: {url}")
    else:
        # Other auth error
        yield format_client_text(f"❌ Authentication failed: {e}")
```

### Logging

```python
import logging
logger = logging.getLogger(__name__)

# Log OAuth events
logger.info("🔐 OAuth URL generated: %s", url)
logger.info("✅ Token received for user: %s", user_id)
logger.debug("Token: %s", token[:20])  # Never log full token
```

---

## Troubleshooting

### Issue: Provider not found

```bash
# List all providers
aws bedrock-agentcore-control list-oauth2-credential-providers \
    --region ap-southeast-2

# Check provider name matches everywhere
grep -r "provider_name\|credential_providers" .
```

### Issue: OAuth URL not generated

```python
# Add logging to callback
def stream_oauth_url_callback(url: str):
    print(f"🔗 OAuth URL: {url}")  # Debug
    oauth_url_queue.put_nowait(url)
```

### Issue: Token not persisted

```python
# Check auth_flow setting
@requires_access_token(
    auth_flow="USER_FEDERATION"  # Must be USER_FEDERATION for persistence
)
```

### Issue: Scopes rejected

```bash
# GitHub: Check OAuth app settings
# Ensure requested scopes are enabled in app configuration

# AWS: Check provider configuration
aws bedrock-agentcore-control get-oauth2-credential-provider \
    --name "github-provider" \
    --region ap-southeast-2
```

---

## Summary

The bedrock-agent-template approach:

1. **Creates OAuth2 Credential Provider** via AWS CLI
2. **Links provider to agent** in `.bedrock_agentcore.yaml`
3. **Uses @requires_access_token** decorator in code
4. **Streams OAuth URLs** back to users for authorization
5. **Gateway is implicit** - auto-created by AgentCore during deployment

This provides a **production-ready, secure OAuth implementation** with minimal code and automatic token management.

---

## Related Files

**Configuration:**
- `agents/github-agent/.bedrock_agentcore.yaml` - Agent OAuth config
- `agents/github-agent/.env` - Local credentials (gitignored)

**Scripts:**
- `agents/github-agent/scripts/setup_github_provider.sh` - Provider setup
- `scripts/configure_agents.sh` - Multi-agent configuration

**Code:**
- `agents/github-agent/src/auth/agentcore.py` - OAuth implementation
- `agents/github-agent/src/auth/__init__.py` - Auth factory
- `agents/github-agent/src/runtime.py` - Runtime integration

**Documentation:**
- `docs/AWS-AgentCore-Setup.md` - Complete setup guide
- `blogs/07-OAUTH_GATEWAY_INTEGRATION.md` - OAuth concepts (draft)

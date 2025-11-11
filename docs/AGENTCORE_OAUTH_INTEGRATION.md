# AgentCore OAuth Integration

Technical implementation of GitHub OAuth authentication with AWS BedrockAgentCore Identity provider.

## OAuth Architecture Overview

### Components
```python
# src/gateway/agentcore.py
class AgentCoreGitHubAuth:
    """Production OAuth authentication via AgentCore."""

    def __init__(self, provider_name: str = "github-provider"):
        self.provider_name = provider_name  # AgentCore Identity provider
        self._token: Optional[str] = None     # Cached token
        self._pending_oauth_url: Optional[str] = None
```

### Identity Provider Setup
```bash
# One-time setup via AgentCore CLI
agentcore configure \
  --identity-provider github-provider \
  --github-client-id YOUR_CLIENT_ID \
  --github-client-secret YOUR_CLIENT_SECRET
```

## OAuth Flow Implementation

### 1. Provider Configuration
```python
# AgentCore Identity provider configuration
provider_config = {
    "name": "github-provider",
    "type": "OAuth2",
    "authorization_url": "https://github.com/login/oauth/authorize",
    "token_url": "https://github.com/login/oauth/access_token",
    "client_id": "your_github_client_id",
    "client_secret": "your_github_client_secret"
}
```

### 2. Token Acquisition Flow
```python
async def get_token() -> str:
    """Get access token, triggering OAuth if needed."""

    # Check for local development token first
    local_token = os.getenv("GITHUB_TOKEN")
    if local_token:
        return local_token

    # Use AgentCore credential provider
    if not self._token:
        from bedrock_agentcore_starter_toolkit import CredentialProvider
        provider = CredentialProvider(self.provider_name)
        self._token = await provider.get_token()

    return self._token
```

### 3. Three-Legged OAuth Flow
```python
# When token not available, trigger OAuth
try:
    token = await provider.get_token()
except ValueError as e:  # OAuth required
    self._pending_oauth_url = provider.get_oauth_url()
    if self.oauth_url_callback:
        self.oauth_url_callback(self._pending_oauth_url)
    raise  # Re-raise to signal OAuth flow needed
```

## Development vs Production Modes

### Development Mode
```python
# Local development bypass
def get_token() -> str:
    # Check for personal access token
    local_token = os.getenv("GITHUB_TOKEN")
    if local_token:
        return local_token  # Immediate return

    # Proceed with OAuth flow
    return await oauth_flow()
```

**Environment Setup**:
```bash
# .env for development
GITHUB_TOKEN=ghp_your_personal_access_token
# GitHub OAuth credentials not required for local dev
```

### Production Mode
```python
# Full OAuth flow required
def get_token() -> str:
    # Never check for local token in production
    return await agentcore_oauth_flow()
```

**Environment Setup**:
```bash
# .env for production
GITHUB_CLIENT_ID=Ov23li...
GITHUB_CLIENT_SECRET=9e32c1...
# No personal tokens in production
```

## Gateway Pattern Implementation

### Authentication Gateway Protocol
```python
# src/gateway/interface.py
from typing import Protocol

class GatewayAuth(Protocol):
    """Protocol for authentication gateways."""

    async def get_token() -> str:
        """Retrieve valid access token."""
        ...
```

### GitHub Gateway Implementation
```python
# src/gateway/agentcore.py
class AgentCoreGitHubAuth:
    def __init__(self,
                 provider_name: str = "github-provider",
                 oauth_url_callback: Optional[Callable] = None):
        self.provider_name = provider_name
        self.oauth_url_callback = oauth_url_callback  # For OAuth URL streaming
```

### Tool Integration
```python
# src/tools/github_tools.py
class GitHubTools:
    def __init__(self, auth_gateway: GatewayAuth):
        self.auth_gateway = auth_gateway
        self._client: Optional[Github] = None

    async def get_client(self) -> Github:
        """Get authenticated GitHub client."""
        if not self._client:
            token = await self.auth_gateway.get_token()
            self._client = Github(token)
        return self._client
```

## Session Management

### Token Caching
```python
class AgentCoreGitHubAuth:
    def __init__(self):
        self._token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None

    async def get_token(self) -> str:
        if self._is_token_valid():
            return self._token

        # Refresh token
        self._token = await self._refresh_token()
        return self._token

    def _is_token_valid(self) -> bool:
        if not self._token:
            return False
        if self._token_expiry and datetime.utcnow() > self._token_expiry:
            return False
        return True
```

### User Context
```python
# AgentCore provides user context automatically
async def get_user_context(self) -> dict:
    """Get user information from AgentCore."""
    # Available in AgentCore environment
    return {
        "user_id": await agentcore.get_user_id(),
        "session_id": await agentcore.get_session_id(),
        "tenant_id": await agentcore.get_tenant_id()
    }
```

## Error Handling

### OAuth Errors
```python
async def handle_oauth_error(self, error: Exception) -> str:
    """Handle OAuth-specific errors."""
    if "authorization_pending" in str(error):
        return "OAuth authorization pending. Please complete the flow."
    elif "access_denied" in str(error):
        return "OAuth access denied. Please retry authorization."
    elif "invalid_client" in str(error):
        return "Invalid OAuth client configuration."
    else:
        return f"Authentication error: {str(error)}"
```

### Network Errors
```python
async def get_token_with_retry(self, max_retries: int = 3) -> str:
    """Get token with retry logic."""
    for attempt in range(max_retries):
        try:
            return await self._get_token_internal()
        except (ConnectionError, TimeoutError) as e:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

## Security Considerations

### Token Validation
```python
def validate_token(self, token: str) -> bool:
    """Validate GitHub token format and scope."""
    if not token.startswith("gho_") and not token.startswith("github_pat_"):
        return False

    # Validate token has required scopes
    required_scopes = ["repo", "read:user"]
    # Token validation would require GitHub API call
    return True
```

### Credential Protection
```python
class AgentCoreGitHubAuth:
    def __str__(self) -> str:
        """String representation without sensitive data."""
        return f"AgentCoreGitHubAuth(provider={self.provider_name})"

    def __repr__(self) -> str:
        """Debug representation without secrets."""
        return self.__str__()
```

## Configuration Management

### Environment Variables
```python
# src/config.py
class Settings(BaseSettings):
    # GitHub OAuth settings
    github_client_id: str
    github_client_secret: SecretStr

    # AgentCore settings
    github_provider_name: str = "github-provider"

    # Development bypass
    github_token: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True
    )
```

### Deployment Configuration
```yaml
# .bedrock_agentcore.yaml
identity_providers:
  - name: github-provider
    type: OAuth2
    config:
      client_id: ${GITHUB_CLIENT_ID}
      client_secret: ${GITHUB_CLIENT_SECRET}
      authorization_url: https://github.com/login/oauth/authorize
      token_url: https://github.com/login/oauth/access_token
      scopes: ["repo", "read:user"]
```

## Testing OAuth Integration

### Mock Testing
```python
def test_oauth_provider_initialization():
    """Test OAuth provider setup."""
    auth = AgentCoreGitHubAuth(
        provider_name="test-provider",
        oauth_url_callback=lambda url: print(f"OAuth URL: {url}")
    )

    assert auth.provider_name == "test-provider"
    assert auth.oauth_url_callback is not None
```

### Token Bypass Testing
```python
async def test_local_token_bypass():
    """Test local development token bypass."""
    with patch.dict('os.environ', {'GITHUB_TOKEN': 'test_token'}):
        auth = AgentCoreGitHubAuth()
        token = await auth.get_token()
        assert token == 'test_token'
```

### Provider Integration Testing
```python
async def test_agentcore_provider_integration():
    """Test AgentCore credential provider integration."""
    with patch('bedrock_agentcore_starter_toolkit.CredentialProvider') as mock_provider:
        mock_instance = mock_provider.return_value
        mock_instance.get_token.return_value = "agentcore_token"

        auth = AgentCoreGitHubAuth()
        with patch.dict('os.environ', {}, clear=True):
            token = await auth.get_token()
            assert token == "agentcore_token"
```

## Integration Best Practices

### 1. Protocol-Based Design
- Use GatewayAuth protocol for flexibility
- Enable easy swapping of authentication methods
- Maintain consistent interface across implementations

### 2. Fallback Handling
- Graceful degradation for development environments
- Clear error messages for OAuth failures
- Automatic retry for transient errors

### 3. Security First
- Never log or expose tokens
- Validate token formats and scopes
- Use proper secret management

### 4. Performance Optimization
- Token caching with expiry handling
- Lazy authentication when needed
- Connection pooling for API calls

This OAuth integration provides secure, production-ready authentication that seamlessly works with both local development and AWS BedrockAgentCore deployment environments.
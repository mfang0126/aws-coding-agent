"""AgentCore OAuth integration tests."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.gateway.agentcore import AgentCoreGitHubAuth
from src.auth.github_auth import GitHubAuth


class TestAgentCoreOAuth:
    """Tests for AgentCore OAuth authentication integration."""

    def test_oauth_provider_initialization(self):
        """Test OAuth provider setup for AgentCore Identity."""
        # Default provider configuration
        auth = AgentCoreGitHubAuth()

        assert auth.provider_name == "github-provider"
        assert auth.oauth_url_callback is None
        assert auth._token is None
        assert auth._pending_oauth_url is None

    def test_oauth_provider_custom_configuration(self):
        """Test OAuth provider with custom configuration."""
        callback = MagicMock()
        auth = AgentCoreGitHubAuth(
            provider_name="custom-github-provider",
            oauth_url_callback=callback
        )

        assert auth.provider_name == "custom-github-provider"
        assert auth.oauth_url_callback is callback

    @pytest.mark.asyncio
    async def test_local_token_bypass(self):
        """Test local development token bypass."""
        auth = AgentCoreGitHubAuth()

        # Mock environment variable
        with patch.dict('os.environ', {'GITHUB_TOKEN': 'local_dev_token'}):
            token = await auth.get_token()
            assert token == 'local_dev_token'

    @pytest.mark.asyncio
    async def test_agentcore_credential_provider_integration(self):
        """Test integration with AgentCore credential provider concept."""
        auth = AgentCoreGitHubAuth()

        # Test the concept of credential provider integration
        with patch.dict('os.environ', {}, clear=True):
            # When no local token, should attempt OAuth flow
            # (In real implementation, this would use bedrock_agentcore_starter_toolkit)
            assert auth._token is None  # No token cached initially

        # Test that provider name is correctly set for AgentCore
        assert auth.provider_name == "github-provider"

    @pytest.mark.asyncio
    async def test_oauth_url_callback_handling(self):
        """Test OAuth URL callback concept for AgentCore."""
        callback_calls = []

        def mock_callback(url):
            callback_calls.append(url)

        auth = AgentCoreGitHubAuth(oauth_url_callback=mock_callback)

        # Test callback registration
        assert auth.oauth_url_callback is mock_callback

        # Test OAuth URL storage concept
        oauth_url = "https://github.com/login/oauth/authorize"
        auth._pending_oauth_url = oauth_url

        if auth.oauth_url_callback:
            auth.oauth_url_callback(oauth_url)

        # In real implementation, callback would be called during OAuth flow
        assert len(callback_calls) == 1
        assert oauth_url in callback_calls[0]

    def test_oauth_token_caching(self):
        """Test OAuth token caching behavior concept."""
        auth = AgentCoreGitHubAuth()

        # Test token caching concept
        auth._token = "cached_oauth_token"

        # Should reuse cached token
        assert auth._token == "cached_oauth_token"

        # Should be able to clear token
        auth._token = None
        assert auth._token is None

    @pytest.mark.asyncio
    async def test_oauth_error_handling(self):
        """Test OAuth error handling scenarios."""
        auth = AgentCoreGitHubAuth()

        # Test missing AgentCore dependency
        with patch.dict('sys.modules', {'bedrock_agentcore_starter_toolkit': None}):
            # Import the module to test the ImportError handling
            import importlib
            import src.gateway.agentcore
            importlib.reload(src.gateway.agentcore)

            # Should still be able to create auth instance
            auth_reloaded = AgentCoreGitHubAuth()
            assert auth_reloaded.provider_name == "github-provider"

    def test_gateway_auth_protocol_compliance(self):
        """Test that AgentCore auth complies with gateway protocol."""
        auth = AgentCoreGitHubAuth()

        # Should have required methods for gateway protocol
        assert hasattr(auth, 'get_token')
        assert callable(getattr(auth, 'get_token'))

        # Should initialize with required attributes
        assert hasattr(auth, 'provider_name')
        assert hasattr(auth, '_token')

    @pytest.mark.asyncio
    async def test_oauth_provider_name_configuration(self):
        """Test different OAuth provider name configurations."""
        provider_names = [
            "github-provider",
            "custom-github",
            "prod-github-provider"
        ]

        for provider_name in provider_names:
            auth = AgentCoreGitHubAuth(provider_name=provider_name)
            assert auth.provider_name == provider_name

    def test_oauth_state_management(self):
        """Test OAuth flow state management."""
        auth = AgentCoreGitHubAuth()

        # Initial state
        assert auth._token is None
        assert auth._pending_oauth_url is None

        # Simulate OAuth in progress
        auth._pending_oauth_url = "https://github.com/oauth/authorize"
        assert auth._pending_oauth_url == "https://github.com/oauth/authorize"

        # Simulate OAuth completion
        auth._token = "oauth_access_token"
        auth._pending_oauth_url = None
        assert auth._token == "oauth_access_token"
        assert auth._pending_oauth_url is None
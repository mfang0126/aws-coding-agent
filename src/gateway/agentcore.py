"""AgentCore OAuth authentication for GitHub."""

import asyncio
import os
from typing import Callable, Optional

try:
    from bedrock_agentcore_starter_toolkit import CredentialProvider
except ImportError:
    # Allow module to load without AgentCore dependencies for testing
    CredentialProvider = None  # type: ignore


class AgentCoreGitHubAuth:
    """Production OAuth authentication via AgentCore.

    Handles OAuth 3-legged flow with user authorization for GitHub.
    Implements the GatewayAuth protocol via structural subtyping.
    """

    def __init__(
        self,
        provider_name: str = "github-provider",
        oauth_url_callback: Optional[Callable[[str], None]] = None,
    ):
        """Initialize OAuth authentication.

        Args:
            provider_name: Credential provider name (default: github-provider)
            oauth_url_callback: Callback for OAuth URL streaming
        """
        self.provider_name = provider_name
        self.oauth_url_callback = oauth_url_callback
        self._token: Optional[str] = None
        self._pending_oauth_url: Optional[str] = None

    async def get_token(self) -> str:
        """Get access token, triggering OAuth if needed.

        Returns:
            str: Valid GitHub access token

        Raises:
            ValueError: If OAuth authorization incomplete
        """
        # Check for local token first (bypass OAuth in dev mode)
        local_token = os.getenv("GITHUB_TOKEN")
        if local_token:
            return local_token

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
            bool: True if token exists (local or OAuth)
        """
        return self._token is not None or os.getenv("GITHUB_TOKEN") is not None

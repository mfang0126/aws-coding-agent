"""
GitHub OAuth authentication using AgentCore Identity.
Based on bedrock-agent-template pattern with @requires_access_token decorator.
"""
import asyncio
import logging
from collections.abc import Callable

from bedrock_agentcore.identity.auth import requires_access_token

logger = logging.getLogger(__name__)


class GitHubAuth:
    """
    GitHub OAuth via AgentCore Identity.
    Implements 3-Legged OAuth (USER_FEDERATION) for per-user tokens.
    """

    def __init__(self, oauth_url_callback: Callable[[str], None] | None = None):
        self._token: str | None = None
        self._oauth_url_callback = oauth_url_callback
        self._pending_oauth_url: str | None = None
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

        Returns:
            GitHub access token

        Raises:
            ValueError: If authentication fails
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

    def get_pending_oauth_url(self) -> str | None:
        """Get pending OAuth URL if available."""
        return self._pending_oauth_url


# Factory function for auth provider
def get_auth_provider(oauth_url_callback: Callable[[str], None] | None = None) -> GitHubAuth:
    """Create GitHub auth provider with optional OAuth URL callback."""
    return GitHubAuth(oauth_url_callback=oauth_url_callback)

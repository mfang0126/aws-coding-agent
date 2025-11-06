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

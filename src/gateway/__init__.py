"""Gateway authentication package for dependency injection."""

from .interface import GatewayAuth
from .agentcore import AgentCoreGitHubAuth

__all__ = [
    "GatewayAuth",
    "AgentCoreGitHubAuth",
]

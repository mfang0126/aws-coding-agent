"""Response formatting and protocols."""

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
    """Format info message.

    Args:
        message: Info message

    Returns:
        Formatted string with emoji
    """
    return f"ℹ️ {message}"


def format_client_text(text: str) -> Dict[str, Any]:
    """Format text for client streaming.

    Args:
        text: Text to format

    Returns:
        Formatted event dict for streaming
    """
    return {
        "type": "text",
        "text": text,
    }


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

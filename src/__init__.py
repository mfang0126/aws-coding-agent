"""AWS Coding Agent package with clean imports."""

# Gateway
from .gateway.interface import GatewayAuth
from .gateway.agentcore import AgentCoreGitHubAuth

# Utils
from .utils.response import (
    AgentResponse,
    format_success,
    format_error,
    format_info,
    format_client_text,
)
from .utils.helpers import extract_text_from_event, log_server

# Constants
from .constants.prompts import (
    CODING_AGENT_SYSTEM_PROMPT,
    PR_REVIEW_PLAN_PROMPT_TEMPLATE,
)
from .constants.messages import (
    ERROR_AUTH_REQUIRED,
    ERROR_NOT_FOUND,
    SUCCESS_CREATED,
    SUCCESS_UPDATED,
    generate_plan_markdown,
    generate_status_json,
)

__all__ = [
    # Gateway
    "GatewayAuth",
    "AgentCoreGitHubAuth",
    # Utils
    "AgentResponse",
    "format_success",
    "format_error",
    "format_info",
    "format_client_text",
    "extract_text_from_event",
    "log_server",
    # Constants
    "CODING_AGENT_SYSTEM_PROMPT",
    "PR_REVIEW_PLAN_PROMPT_TEMPLATE",
    "ERROR_AUTH_REQUIRED",
    "ERROR_NOT_FOUND",
    "SUCCESS_CREATED",
    "SUCCESS_UPDATED",
    "generate_plan_markdown",
    "generate_status_json",
]

"""
Agent factory using functional approach with GitHub authentication.
The Strands Agent class is the only class we use (from library).

Authentication modes:
- Local dev: Uses GITHUB_TOKEN from .env (Personal Access Token)
- Production: Uses OAuth via AgentCore Identity
"""
from strands import Agent
from strands.models import BedrockModel

from ..config import settings
from ..prompts.system_prompts import CODING_AGENT_SYSTEM_PROMPT

# Import the appropriate tools based on auth mode
if settings.github_token:
    # Local mode: use hybrid tools (no OAuth decorator needed)
    from ..tools.github_tools_hybrid import (
        create_github_issue,
        create_pull_request,
        get_repo_info,
        list_github_issues,
        list_github_repos,
    )
else:
    # OAuth mode: use original tools with @requires_access_token
    from ..tools.github_tools import (
        create_github_issue,
        create_pull_request,
        get_repo_info,
        list_github_issues,
        list_github_repos,
    )


def create_coding_agent() -> Agent:
    """
    Create a single Strands Agent with GitHub tools.

    Authentication is hybrid:
    - If GITHUB_TOKEN is set in .env, uses that (local dev)
    - Otherwise, uses OAuth via @requires_access_token (production)

    Returns:
        Configured Strands Agent instance
    """
    # Create Bedrock model
    model = BedrockModel(
        model_id=settings.model_id,
        region_name=settings.aws_region
    )

    # Create agent with GitHub tools
    agent = Agent(
        model=model,
        tools=[
            list_github_repos,
            get_repo_info,
            create_github_issue,
            list_github_issues,
            create_pull_request
        ],
        system_prompt=CODING_AGENT_SYSTEM_PROMPT
    )

    return agent

"""
GitHub tools with hybrid authentication support.

Supports two modes:
1. Local dev: Use GITHUB_TOKEN from .env (Personal Access Token)
2. Production: Use OAuth via AgentCore Identity (@requires_access_token)

The tools automatically detect which mode to use based on config.

This module provides thin decorator wrappers around the core GitHub API
implementations in _github_api.py.
"""
from functools import wraps
from typing import Callable, Any
import logging

from ..config import get_settings
from ._github_api import (
    list_repos_impl,
    get_repo_info_impl,
    create_issue_impl,
    list_issues_impl,
    create_pr_impl
)

logger = logging.getLogger(__name__)


def github_auth_hybrid(scopes: list[str] | None = None):
    """
    Decorator that supports both local token and OAuth authentication.

    Priority:
    1. If GITHUB_TOKEN is set in .env, use it (local dev mode)
    2. Otherwise, require OAuth token via parameter (production mode)

    Args:
        scopes: Required GitHub OAuth scopes (for documentation)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, access_token: str | None = None, **kwargs) -> Any:
            settings = get_settings()

            # Priority 1: Use local token from .env
            if settings.github_token:
                logger.info(
                    "using_local_github_token",
                    function=func.__name__,
                    mode="local_dev"
                )
                token = settings.github_token.get_secret_value()

            # Priority 2: Use OAuth token passed as parameter
            elif access_token:
                logger.info(
                    "using_oauth_token",
                    function=func.__name__,
                    mode="oauth"
                )
                token = access_token

            else:
                error_msg = (
                    "No GitHub authentication available. "
                    "Either set GITHUB_TOKEN in .env or use OAuth flow."
                )
                logger.error("no_github_auth", function=func.__name__)
                raise ValueError(error_msg)

            # Call the actual function with the token
            return await func(*args, access_token=token, **kwargs)

        return wrapper
    return decorator


@github_auth_hybrid(scopes=['repo', 'read:user'])
async def list_github_repos(*, access_token: str, limit: int = 10) -> list[dict]:
    """
    List user's GitHub repositories.

    Auth: Hybrid (local token or OAuth)

    Args:
        access_token: GitHub token (auto-injected by decorator)
        limit: Maximum number of repos to return

    Returns:
        List of repository info dicts
    """
    return await list_repos_impl(access_token, limit)


@github_auth_hybrid(scopes=['repo', 'read:user'])
async def get_repo_info(*, access_token: str, repo_full_name: str) -> dict:
    """
    Get detailed information about a repository.

    Auth: Hybrid (local token or OAuth)

    Args:
        access_token: GitHub token (auto-injected by decorator)
        repo_full_name: Repository full name (e.g., "owner/repo")

    Returns:
        Repository information dict
    """
    return await get_repo_info_impl(access_token, repo_full_name)


@github_auth_hybrid(scopes=['repo'])
async def create_github_issue(
    *,
    access_token: str,
    repo_full_name: str,
    title: str,
    body: str,
    labels: list[str] | None = None
) -> dict:
    """
    Create a new GitHub issue.

    Auth: Hybrid (local token or OAuth)

    Args:
        access_token: GitHub token (auto-injected by decorator)
        repo_full_name: Repository full name (e.g., "owner/repo")
        title: Issue title
        body: Issue body/description
        labels: Optional list of label names

    Returns:
        Created issue info dict
    """
    return await create_issue_impl(access_token, repo_full_name, title, body, labels)


@github_auth_hybrid(scopes=['repo', 'read:user'])
async def list_github_issues(
    *,
    access_token: str,
    repo_full_name: str,
    state: str = 'open',
    limit: int = 10
) -> list[dict]:
    """
    List issues for a repository.

    Auth: Hybrid (local token or OAuth)

    Args:
        access_token: GitHub token (auto-injected by decorator)
        repo_full_name: Repository full name (e.g., "owner/repo")
        state: Issue state ("open", "closed", "all")
        limit: Maximum number of issues to return

    Returns:
        List of issue info dicts
    """
    return await list_issues_impl(access_token, repo_full_name, state, limit)


@github_auth_hybrid(scopes=['repo'])
async def create_pull_request(
    *,
    access_token: str,
    repo_full_name: str,
    title: str,
    body: str,
    head: str,
    base: str = 'main'
) -> dict:
    """
    Create a new pull request.

    Auth: Hybrid (local token or OAuth)

    Args:
        access_token: GitHub token (auto-injected by decorator)
        repo_full_name: Repository full name (e.g., "owner/repo")
        title: PR title
        body: PR description
        head: Head branch name (source branch)
        base: Base branch name (target branch, default: 'main')

    Returns:
        Created PR info dict
    """
    return await create_pr_impl(access_token, repo_full_name, title, body, head, base)

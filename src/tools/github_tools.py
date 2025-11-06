"""
GitHub tools using authenticated API.
Each tool uses @requires_access_token for OAuth authentication.

This module provides thin decorator wrappers around the core GitHub API
implementations in _github_api.py.
"""
from bedrock_agentcore.identity.auth import requires_access_token

from ._github_api import (
    list_repos_impl,
    get_repo_info_impl,
    create_issue_impl,
    list_issues_impl,
    create_pr_impl
)


@requires_access_token(
    provider_name='github-provider',
    scopes=['repo', 'read:user'],
    auth_flow='USER_FEDERATION'
)
async def list_github_repos(*, access_token: str, limit: int = 10) -> list[dict]:
    """
    List user's GitHub repositories.

    Args:
        access_token: GitHub OAuth token (injected by decorator)
        limit: Maximum number of repos to return

    Returns:
        List of repository info dicts
    """
    return await list_repos_impl(access_token, limit)


@requires_access_token(
    provider_name='github-provider',
    scopes=['repo', 'read:user'],
    auth_flow='USER_FEDERATION'
)
async def get_repo_info(*, access_token: str, repo_full_name: str) -> dict:
    """
    Get detailed information about a repository.

    Args:
        access_token: GitHub OAuth token (injected by decorator)
        repo_full_name: Repository full name (e.g., "owner/repo")

    Returns:
        Repository information dict
    """
    return await get_repo_info_impl(access_token, repo_full_name)


@requires_access_token(
    provider_name='github-provider',
    scopes=['repo'],
    auth_flow='USER_FEDERATION'
)
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

    Args:
        access_token: GitHub OAuth token (injected by decorator)
        repo_full_name: Repository full name (e.g., "owner/repo")
        title: Issue title
        body: Issue body/description
        labels: Optional list of label names

    Returns:
        Created issue info dict
    """
    return await create_issue_impl(access_token, repo_full_name, title, body, labels)


@requires_access_token(
    provider_name='github-provider',
    scopes=['repo', 'read:user'],
    auth_flow='USER_FEDERATION'
)
async def list_github_issues(
    *,
    access_token: str,
    repo_full_name: str,
    state: str = 'open',
    limit: int = 10
) -> list[dict]:
    """
    List issues for a repository.

    Args:
        access_token: GitHub OAuth token (injected by decorator)
        repo_full_name: Repository full name (e.g., "owner/repo")
        state: Issue state ("open", "closed", "all")
        limit: Maximum number of issues to return

    Returns:
        List of issue info dicts
    """
    return await list_issues_impl(access_token, repo_full_name, state, limit)


@requires_access_token(
    provider_name='github-provider',
    scopes=['repo'],
    auth_flow='USER_FEDERATION'
)
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

    Args:
        access_token: GitHub OAuth token (injected by decorator)
        repo_full_name: Repository full name (e.g., "owner/repo")
        title: PR title
        body: PR description
        head: Head branch name (source branch)
        base: Base branch name (target branch, default: 'main')

    Returns:
        Created PR info dict
    """
    return await create_pr_impl(access_token, repo_full_name, title, body, head, base)

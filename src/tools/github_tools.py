"""
GitHub tools using authenticated API.
Each tool uses @requires_access_token for OAuth authentication.
"""
import logging

from bedrock_agentcore.identity.auth import requires_access_token
from github import Github

logger = logging.getLogger(__name__)


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
    logger.info("listing_repos", limit=limit)

    try:
        g = Github(access_token)
        user = g.get_user()

        repos = []
        for repo in user.get_repos()[:limit]:
            repos.append({
                "name": repo.name,
                "full_name": repo.full_name,
                "description": repo.description,
                "url": repo.html_url,
                "private": repo.private,
                "language": repo.language,
                "stars": repo.stargazers_count
            })

        logger.info("repos_listed", count=len(repos))
        return repos

    except Exception as e:
        logger.error("list_repos_failed", error=str(e))
        raise


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
    logger.info("getting_repo_info", repo=repo_full_name)

    try:
        g = Github(access_token)
        repo = g.get_repo(repo_full_name)

        info = {
            "name": repo.name,
            "full_name": repo.full_name,
            "description": repo.description,
            "url": repo.html_url,
            "private": repo.private,
            "language": repo.language,
            "stars": repo.stargazers_count,
            "forks": repo.forks_count,
            "open_issues": repo.open_issues_count,
            "default_branch": repo.default_branch,
            "created_at": repo.created_at.isoformat(),
            "updated_at": repo.updated_at.isoformat()
        }

        logger.info("repo_info_retrieved", repo=repo_full_name)
        return info

    except Exception as e:
        logger.error("get_repo_info_failed", repo=repo_full_name, error=str(e))
        raise


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
    logger.info("creating_issue", repo=repo_full_name, title=title)

    try:
        g = Github(access_token)
        repo = g.get_repo(repo_full_name)

        issue = repo.create_issue(
            title=title,
            body=body,
            labels=labels or []
        )

        info = {
            "number": issue.number,
            "title": issue.title,
            "body": issue.body,
            "url": issue.html_url,
            "state": issue.state,
            "created_at": issue.created_at.isoformat()
        }

        logger.info("issue_created", repo=repo_full_name, issue_number=issue.number)
        return info

    except Exception as e:
        logger.error("create_issue_failed", repo=repo_full_name, error=str(e))
        raise


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
    logger.info("listing_issues", repo=repo_full_name, state=state, limit=limit)

    try:
        g = Github(access_token)
        repo = g.get_repo(repo_full_name)

        issues = []
        for issue in repo.get_issues(state=state)[:limit]:
            # Skip pull requests (they appear as issues in GitHub API)
            if issue.pull_request:
                continue

            issues.append({
                "number": issue.number,
                "title": issue.title,
                "body": issue.body,
                "url": issue.html_url,
                "state": issue.state,
                "labels": [label.name for label in issue.labels],
                "created_at": issue.created_at.isoformat(),
                "updated_at": issue.updated_at.isoformat()
            })

        logger.info("issues_listed", repo=repo_full_name, count=len(issues))
        return issues

    except Exception as e:
        logger.error("list_issues_failed", repo=repo_full_name, error=str(e))
        raise


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
    logger.info("creating_pr", repo=repo_full_name, title=title, head=head, base=base)

    try:
        g = Github(access_token)
        repo = g.get_repo(repo_full_name)

        pr = repo.create_pull(
            title=title,
            body=body,
            head=head,
            base=base
        )

        info = {
            "number": pr.number,
            "title": pr.title,
            "body": pr.body,
            "url": pr.html_url,
            "state": pr.state,
            "head": pr.head.ref,
            "base": pr.base.ref,
            "created_at": pr.created_at.isoformat()
        }

        logger.info("pr_created", repo=repo_full_name, pr_number=pr.number)
        return info

    except Exception as e:
        logger.error("create_pr_failed", repo=repo_full_name, error=str(e))
        raise

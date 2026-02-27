"""PyGitHub wrapper — authenticated client for GitHub API operations."""

from __future__ import annotations

import logging
import os

from github import Auth, Github
from github.Repository import Repository

logger = logging.getLogger(__name__)

_client: Github | None = None


def get_client() -> Github:
    """Get or create an authenticated GitHub client."""
    global _client
    if _client is None:
        token = os.environ.get("GITHUB_TOKEN", "")
        if not token:
            raise EnvironmentError(
                "GITHUB_TOKEN environment variable is required for GitHub integration"
            )
        auth = Auth.Token(token)
        _client = Github(auth=auth)
    return _client


def get_repo(owner_repo: str) -> Repository:
    """Get a repository by 'owner/repo' string."""
    return get_client().get_repo(owner_repo)


def close_client() -> None:
    """Close the GitHub client connection."""
    global _client
    if _client is not None:
        _client.close()
        _client = None

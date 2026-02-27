"""GitHub Pull Requests — create, label, review, and merge PRs."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from devlution.integrations.github.client import get_repo

logger = logging.getLogger(__name__)


@dataclass
class PRResult:
    number: int
    url: str
    title: str
    state: str = "open"


def create_pr(
    owner_repo: str,
    title: str,
    body: str,
    head: str,
    base: str = "main",
    labels: list[str] | None = None,
    draft: bool = False,
) -> PRResult:
    """Create a pull request and optionally apply labels."""
    repo = get_repo(owner_repo)

    pr = repo.create_pull(
        title=title,
        body=body,
        head=head,
        base=base,
        draft=draft,
    )

    if labels:
        pr.add_to_labels(*labels)

    logger.info("Created PR #%d: %s", pr.number, pr.html_url)
    return PRResult(
        number=pr.number,
        url=pr.html_url,
        title=pr.title,
        state=pr.state,
    )


def add_review_comment(
    owner_repo: str,
    pr_number: int,
    body: str,
    commit_sha: str,
    path: str,
    line: int,
) -> None:
    """Add a review comment at a specific line in a PR."""
    repo = get_repo(owner_repo)
    pr = repo.get_pull(pr_number)
    commit = repo.get_commit(commit_sha)
    pr.create_review_comment(
        body=body,
        commit=commit,
        path=path,
        line=line,
    )
    logger.info("Added review comment to PR #%d at %s:%d", pr_number, path, line)


def request_reviewers(
    owner_repo: str,
    pr_number: int,
    reviewers: list[str],
) -> None:
    """Request specific reviewers for a PR."""
    repo = get_repo(owner_repo)
    pr = repo.get_pull(pr_number)
    pr.create_review_request(reviewers=reviewers)
    logger.info("Requested reviewers %s for PR #%d", reviewers, pr_number)


def merge_pr(
    owner_repo: str,
    pr_number: int,
    merge_method: str = "squash",
    commit_message: str | None = None,
) -> bool:
    """Merge a pull request."""
    repo = get_repo(owner_repo)
    pr = repo.get_pull(pr_number)

    if not pr.mergeable:
        logger.warning("PR #%d is not mergeable", pr_number)
        return False

    pr.merge(
        merge_method=merge_method,
        commit_message=commit_message or pr.title,
    )
    logger.info("Merged PR #%d via %s", pr_number, merge_method)
    return True


def add_labels(owner_repo: str, pr_number: int, labels: list[str]) -> None:
    """Add labels to a pull request."""
    repo = get_repo(owner_repo)
    pr = repo.get_pull(pr_number)
    pr.add_to_labels(*labels)

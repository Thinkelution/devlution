"""GitHub Issues — fetch, comment, and close issues."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from devlution.integrations.github.client import get_repo

logger = logging.getLogger(__name__)


@dataclass
class IssueContext:
    number: int
    title: str
    body: str
    labels: list[str] = field(default_factory=list)
    state: str = "open"
    comments: list[str] = field(default_factory=list)
    linked_prs: list[int] = field(default_factory=list)


def get_issue(owner_repo: str, issue_number: int) -> IssueContext:
    """Fetch a GitHub issue with full context."""
    repo = get_repo(owner_repo)
    issue = repo.get_issue(number=issue_number)

    comments = [c.body for c in issue.get_comments()]
    labels = [l.name for l in issue.labels]

    return IssueContext(
        number=issue.number,
        title=issue.title,
        body=issue.body or "",
        labels=labels,
        state=issue.state,
        comments=comments,
    )


def add_comment(owner_repo: str, issue_number: int, body: str) -> None:
    """Add a comment to a GitHub issue."""
    repo = get_repo(owner_repo)
    issue = repo.get_issue(number=issue_number)
    issue.create_comment(body)
    logger.info("Added comment to issue #%d", issue_number)


def close_issue(owner_repo: str, issue_number: int, comment: str | None = None) -> None:
    """Close a GitHub issue, optionally with a closing comment."""
    repo = get_repo(owner_repo)
    issue = repo.get_issue(number=issue_number)
    if comment:
        issue.create_comment(comment)
    issue.edit(state="closed")
    logger.info("Closed issue #%d", issue_number)


def add_labels(owner_repo: str, issue_number: int, labels: list[str]) -> None:
    """Add labels to a GitHub issue."""
    repo = get_repo(owner_repo)
    issue = repo.get_issue(number=issue_number)
    for label in labels:
        issue.add_to_labels(label)
    logger.info("Added labels %s to issue #%d", labels, issue_number)

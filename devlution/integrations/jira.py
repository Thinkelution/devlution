"""Jira integration — optional ticket sync with pipeline state.

Provides basic ticket creation and status updates via the Jira REST API.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any

import requests

logger = logging.getLogger(__name__)


@dataclass
class JiraTicket:
    key: str
    summary: str
    status: str
    url: str


def _get_config() -> tuple[str, str, str]:
    """Get Jira connection details from environment."""
    base_url = os.environ.get("JIRA_BASE_URL", "")
    email = os.environ.get("JIRA_EMAIL", "")
    token = os.environ.get("JIRA_API_TOKEN", "")
    if not all([base_url, email, token]):
        raise EnvironmentError(
            "JIRA_BASE_URL, JIRA_EMAIL, and JIRA_API_TOKEN are required"
        )
    return base_url, email, token


def create_ticket(
    project_key: str,
    summary: str,
    description: str,
    issue_type: str = "Task",
) -> JiraTicket:
    """Create a new Jira ticket."""
    base_url, email, token = _get_config()

    response = requests.post(
        f"{base_url}/rest/api/3/issue",
        auth=(email, token),
        json={
            "fields": {
                "project": {"key": project_key},
                "summary": summary,
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": description}],
                        }
                    ],
                },
                "issuetype": {"name": issue_type},
            }
        },
        timeout=15,
    )
    response.raise_for_status()
    data = response.json()
    key = data["key"]

    return JiraTicket(
        key=key,
        summary=summary,
        status="To Do",
        url=f"{base_url}/browse/{key}",
    )


def update_status(ticket_key: str, transition_name: str) -> bool:
    """Transition a Jira ticket to a new status."""
    base_url, email, token = _get_config()

    transitions_resp = requests.get(
        f"{base_url}/rest/api/3/issue/{ticket_key}/transitions",
        auth=(email, token),
        timeout=15,
    )
    transitions_resp.raise_for_status()

    transition_id = None
    for t in transitions_resp.json().get("transitions", []):
        if t["name"].lower() == transition_name.lower():
            transition_id = t["id"]
            break

    if not transition_id:
        logger.warning("Transition '%s' not found for %s", transition_name, ticket_key)
        return False

    requests.post(
        f"{base_url}/rest/api/3/issue/{ticket_key}/transitions",
        auth=(email, token),
        json={"transition": {"id": transition_id}},
        timeout=15,
    )
    logger.info("Transitioned %s to %s", ticket_key, transition_name)
    return True


def add_comment(ticket_key: str, comment: str) -> None:
    """Add a comment to a Jira ticket."""
    base_url, email, token = _get_config()

    requests.post(
        f"{base_url}/rest/api/3/issue/{ticket_key}/comment",
        auth=(email, token),
        json={
            "body": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": comment}],
                    }
                ],
            }
        },
        timeout=15,
    )
    logger.info("Added comment to %s", ticket_key)

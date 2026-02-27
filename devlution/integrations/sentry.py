"""Sentry integration — fetch error events for the Debugger Agent.

Connects to the Sentry API to pull recent error events and parse them
into structured failure logs.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Any

import requests

logger = logging.getLogger(__name__)

SENTRY_API_BASE = "https://sentry.io/api/0"


@dataclass
class SentryEvent:
    event_id: str
    title: str
    message: str
    level: str
    platform: str
    stacktrace: str = ""
    tags: dict[str, str] = field(default_factory=dict)
    timestamp: str = ""


def get_auth_token() -> str:
    token = os.environ.get("SENTRY_AUTH_TOKEN", "")
    if not token:
        raise EnvironmentError("SENTRY_AUTH_TOKEN environment variable is required")
    return token


def fetch_recent_events(
    org_slug: str,
    project_slug: str,
    limit: int = 10,
) -> list[SentryEvent]:
    """Fetch recent error events from Sentry."""
    token = get_auth_token()
    url = f"{SENTRY_API_BASE}/projects/{org_slug}/{project_slug}/events/"

    response = requests.get(
        url,
        headers={"Authorization": f"Bearer {token}"},
        params={"per_page": limit},
        timeout=15,
    )
    response.raise_for_status()

    events: list[SentryEvent] = []
    for raw in response.json():
        stacktrace = ""
        entries = raw.get("entries", [])
        for entry in entries:
            if entry.get("type") == "exception":
                frames = (
                    entry.get("data", {})
                    .get("values", [{}])[0]
                    .get("stacktrace", {})
                    .get("frames", [])
                )
                stacktrace = "\n".join(
                    f"  {f.get('filename', '?')}:{f.get('lineNo', '?')} in {f.get('function', '?')}"
                    for f in frames
                )

        events.append(
            SentryEvent(
                event_id=raw.get("eventID", ""),
                title=raw.get("title", ""),
                message=raw.get("message", ""),
                level=raw.get("level", "error"),
                platform=raw.get("platform", ""),
                stacktrace=stacktrace,
                tags={t["key"]: t["value"] for t in raw.get("tags", [])},
                timestamp=raw.get("dateCreated", ""),
            )
        )

    return events


def event_to_failure_log(event: SentryEvent) -> str:
    """Convert a Sentry event into a text failure log for the Debugger Agent."""
    parts = [
        f"Error: {event.title}",
        f"Level: {event.level}",
        f"Platform: {event.platform}",
        f"Message: {event.message}",
    ]
    if event.stacktrace:
        parts.append(f"Stacktrace:\n{event.stacktrace}")
    return "\n".join(parts)

"""Slack integration — approval request messages and pipeline notifications.

Uses Slack Bolt SDK for sending interactive messages with approve/reject buttons.
"""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

_app = None


def get_app():
    """Lazily initialize the Slack Bolt app."""
    global _app
    if _app is None:
        token = os.environ.get("DEVLUTION_SLACK_TOKEN", "")
        if not token:
            logger.warning("DEVLUTION_SLACK_TOKEN not set — Slack integration disabled")
            return None

        from slack_bolt import App
        _app = App(token=token)
    return _app


def send_approval_request(
    channel: str,
    summary: str,
    gate_id: str,
    pipeline_id: str,
    context_url: str = "",
) -> bool:
    """Send an interactive approval request to a Slack channel."""
    app = get_app()
    if app is None:
        logger.info("[slack-stub] Approval request for gate %s: %s", gate_id, summary)
        return False

    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "Devlution — Approval Required"},
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": summary},
        },
    ]

    if context_url:
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"<{context_url}|View PR>"},
        })

    blocks.append({
        "type": "actions",
        "elements": [
            {
                "type": "button",
                "text": {"type": "plain_text", "text": "Approve"},
                "style": "primary",
                "action_id": f"devlution_approve_{gate_id}",
                "value": f"{pipeline_id}:{gate_id}:approved",
            },
            {
                "type": "button",
                "text": {"type": "plain_text", "text": "Reject"},
                "style": "danger",
                "action_id": f"devlution_reject_{gate_id}",
                "value": f"{pipeline_id}:{gate_id}:rejected",
            },
        ],
    })

    try:
        app.client.chat_postMessage(channel=channel, blocks=blocks, text=summary)
        logger.info("Sent approval request to %s for gate %s", channel, gate_id)
        return True
    except Exception as e:
        logger.error("Failed to send Slack message: %s", e)
        return False


def send_notification(channel: str, message: str) -> bool:
    """Send a simple text notification to a Slack channel."""
    app = get_app()
    if app is None:
        logger.info("[slack-stub] Notification: %s", message)
        return False

    try:
        app.client.chat_postMessage(channel=channel, text=message)
        return True
    except Exception as e:
        logger.error("Failed to send Slack notification: %s", e)
        return False

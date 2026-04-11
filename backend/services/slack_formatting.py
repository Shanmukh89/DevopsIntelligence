"""Slack Block Kit helpers: severity colors, buttons, timestamps."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal
from urllib.parse import urlencode

Severity = Literal["critical", "warning", "info", "success"]


def severity_color(severity: Severity) -> str:
    """Attachment color for message (legacy) or section context."""
    return {
        "critical": "#E01E5A",
        "warning": "#ECB22E",
        "info": "#36C5F0",
        "success": "#2EB67D",
    }[severity]


def now_footer_text() -> str:
    ts = datetime.now(tz=UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
    return f"Sent at {ts}"


def action_buttons(
    *,
    github_url: str | None,
    auditr_url: str,
    dismiss_value: str,
    include_dismiss: bool = True,
) -> dict[str, Any]:
    """Primary actions row: GitHub, Auditr, optional Dismiss (interactive)."""
    elements: list[dict[str, Any]] = []
    if github_url:
        elements.append(
            {
                "type": "button",
                "text": {"type": "plain_text", "text": "View in GitHub", "emoji": True},
                "url": github_url,
                "action_id": "open_github",
            }
        )
    elements.append(
        {
            "type": "button",
            "text": {"type": "plain_text", "text": "View in Auditr", "emoji": True},
            "url": auditr_url,
            "action_id": "open_auditr",
        }
    )
    if include_dismiss:
        elements.append(
            {
                "type": "button",
                "text": {"type": "plain_text", "text": "Dismiss Alert", "emoji": True},
                "style": "danger",
                "action_id": "dismiss_alert",
                "value": dismiss_value[:2000],
            }
        )
    return {"type": "actions", "elements": elements}


def trackable_github_button(*, track_base_url: str, github_url: str) -> dict[str, Any]:
    """
    Button that routes through our tracking redirect (logs analytics) then to GitHub.
    Use when you need server-side analytics on clicks.
    """
    q = urlencode({"u": github_url})
    return {
        "type": "button",
        "text": {"type": "plain_text", "text": "View in GitHub", "emoji": True},
        "url": f"{track_base_url.rstrip('/')}/api/integrations/slack/track?{q}",
        "action_id": "track_github",
    }


def divider() -> dict[str, Any]:
    return {"type": "divider"}


def context_block(text: str) -> dict[str, Any]:
    return {
        "type": "context",
        "elements": [{"type": "mrkdwn", "text": text}],
    }


def header_block(text: str) -> dict[str, Any]:
    return {"type": "header", "text": {"type": "plain_text", "text": text, "emoji": True}}


def section_mrkdwn(text: str) -> dict[str, Any]:
    return {"type": "section", "text": {"type": "mrkdwn", "text": text}}


def attachment_with_color(color: str, blocks: list[dict[str, Any]]) -> dict[str, Any]:
    """Legacy attachment wrapper for left border color in Slack clients."""
    return {"color": color, "blocks": blocks}

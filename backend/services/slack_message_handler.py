"""Slack interactive payloads: dismiss alerts, acknowledge analytics (no secrets logged)."""

from __future__ import annotations

import logging
import uuid
from typing import Any

from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import BaseAppSettings
from models.slack_integration import SlackAlertDismissal, SlackIntegration
from models.vulnerabilities import VulnerabilityAlert

logger = logging.getLogger(__name__)


def decode_slack_oauth_state(token: str, settings: BaseAppSettings) -> tuple[uuid.UUID, str]:
    """Decode team id and redirect_uri from signed OAuth state JWT."""
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as e:
        raise ValueError("invalid state") from e
    if not payload.get("slack_oauth"):
        raise ValueError("invalid state")
    redirect_uri = payload.get("redirect_uri") or ""
    if not redirect_uri:
        raise ValueError("invalid state")
    return uuid.UUID(payload["sub"]), str(redirect_uri)


async def handle_interactive_payload(
    *,
    session: AsyncSession,
    settings: BaseAppSettings,
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Process block_actions from Slack interactivity."""
    slack_team_id = (payload.get("team") or {}).get("id")
    if not slack_team_id:
        return {"text": "Missing team context.", "response_type": "ephemeral"}

    r = await session.execute(select(SlackIntegration).where(SlackIntegration.workspace_id == slack_team_id))
    integration = r.scalar_one_or_none()
    if not integration:
        return {"text": "Auditr is not connected for this workspace.", "response_type": "ephemeral"}

    actions = payload.get("actions") or []
    if not actions:
        return {"text": "No actions.", "response_type": "ephemeral"}

    action = actions[0]
    action_id = action.get("action_id", "")

    if action_id == "dismiss_alert":
        raw = action.get("value") or ""
        return await _dismiss_from_value(session, integration.team_id, raw)

    if action_id == "open_github":
        # URL buttons do not always POST; no-op
        return {"delete_original": False}

    if action_id == "open_auditr":
        return {"delete_original": False}

    return {"text": "Unknown action.", "response_type": "ephemeral"}


async def _dismiss_from_value(
    session: AsyncSession,
    team_id: uuid.UUID,
    raw: str,
) -> dict[str, Any]:
    parts = raw.split("|")
    if len(parts) < 4 or parts[0] != "dismiss":
        return {"text": "Invalid dismiss payload.", "response_type": "ephemeral"}

    kind = parts[1]
    try:
        ref_id = uuid.UUID(parts[3]) if len(parts[3]) == 36 else None
    except ValueError:
        ref_id = None

    repo_part = parts[2]
    try:
        repo_uuid = uuid.UUID(repo_part)
    except ValueError:
        repo_uuid = None

    alert_ref = "|".join(parts[1:])[:512]
    existing = await session.execute(
        select(SlackAlertDismissal).where(
            SlackAlertDismissal.team_id == team_id,
            SlackAlertDismissal.alert_kind == kind,
            SlackAlertDismissal.alert_ref == alert_ref,
        )
    )
    if existing.scalar_one_or_none():
        return {"text": "Already dismissed.", "response_type": "ephemeral"}

    session.add(
        SlackAlertDismissal(
            team_id=team_id,
            alert_kind=kind,
            alert_ref=alert_ref,
        )
    )

    if kind == "vuln" and repo_uuid and ref_id:
        alert = await session.get(VulnerabilityAlert, ref_id)
        if alert and alert.repository_id == repo_uuid:
            alert.status = "dismissed"

    await session.flush()
    logger.info(
        "slack_alert_dismissed",
        extra={"team_id": str(team_id), "kind": kind, "action_taken": "dismiss"},
    )
    return {"text": "Alert dismissed in Auditr.", "response_type": "ephemeral"}



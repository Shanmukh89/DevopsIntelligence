"""Slack workspace integration and notification thread tracking."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import ForeignKey, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import BaseModel
from models.teams import Team


class SlackIntegration(BaseModel):
    """Per-team Slack connection (OAuth bot or incoming webhook)."""

    __tablename__ = "slack_integrations"
    __table_args__ = (UniqueConstraint("team_id", name="uq_slack_integrations_team_id"),)

    team_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    workspace_id: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    workspace_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # "oauth" | "webhook"
    integration_type: Mapped[str] = mapped_column(String(32), nullable=False, default="oauth")
    bot_token_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    webhook_url_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)

    default_channel: Mapped[str | None] = mapped_column(String(128), nullable=True)
    # e.g. {"builds": "C123", "security": "C456"}
    channels_config: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    team: Mapped["Team"] = relationship("Team")


class SlackNotificationThread(BaseModel):
    """Maps a logical key (e.g. same commit) to a root message for updates/threading."""

    __tablename__ = "slack_notification_threads"
    __table_args__ = (UniqueConstraint("team_id", "dedupe_key", name="uq_slack_threads_team_dedupe"),)

    team_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    slack_integration_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("slack_integrations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    dedupe_key: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    channel_id: Mapped[str] = mapped_column(String(32), nullable=False)
    message_ts: Mapped[str] = mapped_column(String(32), nullable=False)


class SlackAlertDismissal(BaseModel):
    """User dismissed an alert from Slack (interactive)."""

    __tablename__ = "slack_alert_dismissals"
    __table_args__ = (
        UniqueConstraint("team_id", "alert_kind", "alert_ref", name="uq_slack_dismissals_ref"),
    )

    team_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    alert_kind: Mapped[str] = mapped_column(String(64), nullable=False)
    alert_ref: Mapped[str] = mapped_column(String(512), nullable=False, index=True)

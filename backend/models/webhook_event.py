"""Webhook audit log stored in the database."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from database import BaseModel


class WebhookEvent(BaseModel):
    """Record of each GitHub webhook received (and dispatch outcome)."""

    __tablename__ = "webhook_events"

    event_type: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    delivery_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    action: Mapped[str | None] = mapped_column(String(64), nullable=True)
    repository_full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    payload_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    payload_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    processing_note: Mapped[str | None] = mapped_column(String(512), nullable=True)
    received_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

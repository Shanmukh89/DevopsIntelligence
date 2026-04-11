"""Dependency vulnerability alerts."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import BaseModel
from models.repositories import Repository
from models.teams import SoftDeleteMixin

if TYPE_CHECKING:
    pass


class VulnerabilityAlert(BaseModel, SoftDeleteMixin):
    """Known CVE / advisory affecting a repository dependency."""

    __tablename__ = "vulnerability_alerts"

    repository_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("repositories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    package_name: Mapped[str] = mapped_column(String(255), nullable=False)
    installed_version: Mapped[str | None] = mapped_column(String(100), nullable=True)
    patched_version: Mapped[str | None] = mapped_column(String(100), nullable=True)
    cve_id: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    ghsa_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    severity: Mapped[str | None] = mapped_column(String(20), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="open")
    detected_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    repository: Mapped["Repository"] = relationship(back_populates="vulnerability_alerts")

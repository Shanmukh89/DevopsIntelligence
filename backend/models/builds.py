"""CI build runs and raw log lines."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import BaseModel
from models.repositories import Repository
from models.teams import SoftDeleteMixin

if TYPE_CHECKING:
    pass


class Build(BaseModel, SoftDeleteMixin):
    """GitHub Actions (or other CI) workflow run."""

    __tablename__ = "builds"
    __table_args__ = (UniqueConstraint("github_run_id", name="uq_builds_github_run_id"),)

    repository_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("repositories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    github_run_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    branch: Mapped[str | None] = mapped_column(String(100), nullable=True)
    commit_sha: Mapped[str | None] = mapped_column(String(40), nullable=True)
    author_github_login: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    ai_explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    stackoverflow_results: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    repository: Mapped["Repository"] = relationship(back_populates="builds")
    logs: Mapped[list["BuildLog"]] = relationship(
        back_populates="build",
        cascade="all, delete-orphan",
        order_by="BuildLog.sequence",
    )


class BuildLog(BaseModel):
    """Structured slice of CI log output."""

    __tablename__ = "build_logs"

    build_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("builds.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sequence: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    line_text: Mapped[str] = mapped_column(Text, nullable=False)
    log_level: Mapped[str | None] = mapped_column(String(32), nullable=True)

    build: Mapped["Build"] = relationship(back_populates="logs")

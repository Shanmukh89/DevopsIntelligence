"""AI PR review records and structured issues."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import BaseModel
from models.repositories import Repository
from models.teams import SoftDeleteMixin

if TYPE_CHECKING:
    pass


class PRReview(BaseModel, SoftDeleteMixin):
    """One automated review run for a pull request."""

    __tablename__ = "pr_reviews"

    repository_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("repositories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    pr_number: Mapped[int] = mapped_column(Integer, nullable=False)
    pr_title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    author_github_login: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    issues_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    review_body: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    repository: Mapped["Repository"] = relationship(back_populates="pr_reviews")
    issues: Mapped[list["PRIssue"]] = relationship(
        back_populates="pr_review",
        cascade="all, delete-orphan",
    )


class PRIssue(BaseModel):
    """Single finding from a PR review."""

    __tablename__ = "pr_issues"

    pr_review_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("pr_reviews.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    severity: Mapped[str | None] = mapped_column(String(20), nullable=True)
    category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    line_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    suggestion: Mapped[str | None] = mapped_column(Text, nullable=True)

    pr_review: Mapped["PRReview"] = relationship(back_populates="issues")

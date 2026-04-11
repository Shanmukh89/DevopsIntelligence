"""Semantic duplicate code pairs."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import BaseModel
from models.repositories import Repository
from models.teams import SoftDeleteMixin

if TYPE_CHECKING:
    pass


class CodeClone(BaseModel, SoftDeleteMixin):
    """Potential clone pair surfaced by embedding similarity."""

    __tablename__ = "code_clones"

    repository_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("repositories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    file_path_a: Mapped[str | None] = mapped_column(String(500), nullable=True)
    start_line_a: Mapped[int | None] = mapped_column(Integer, nullable=True)
    file_path_b: Mapped[str | None] = mapped_column(String(500), nullable=True)
    start_line_b: Mapped[int | None] = mapped_column(Integer, nullable=True)
    similarity_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    detected_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    repository: Mapped["Repository"] = relationship(back_populates="code_clones")

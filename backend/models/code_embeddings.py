"""Code chunks and pgvector embeddings for RAG."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import BaseModel
from models.repositories import Repository
from models.teams import SoftDeleteMixin

if TYPE_CHECKING:
    pass


class CodeEmbedding(BaseModel, SoftDeleteMixin):
    """Indexed code chunk with embedding vector (cosine search)."""

    __tablename__ = "code_embeddings"

    repository_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("repositories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    start_line: Mapped[int] = mapped_column(Integer, nullable=False)
    end_line: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(1536), nullable=False)
    language: Mapped[str | None] = mapped_column(String(50), nullable=True)
    last_updated: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    repository: Mapped["Repository"] = relationship(back_populates="code_embeddings")

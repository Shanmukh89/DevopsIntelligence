"""LLM-generated documentation snapshots."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import BaseModel
from models.repositories import Repository
from models.teams import SoftDeleteMixin

if TYPE_CHECKING:
    pass


class GeneratedDocumentation(BaseModel, SoftDeleteMixin):
    """Stored docstring / markdown produced for a symbol or file."""

    __tablename__ = "generated_documentation"

    repository_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("repositories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    symbol_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    doc_content: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str | None] = mapped_column(String(50), nullable=True)

    repository: Mapped["Repository"] = relationship(back_populates="generated_documentation")

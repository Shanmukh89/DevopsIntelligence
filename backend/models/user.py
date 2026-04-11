"""Application user (linked to GitHub identity)."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import BaseModel

if TYPE_CHECKING:
    from models.github_credentials import GitHubCredential
    from models.teams import Team


class User(BaseModel):
    __tablename__ = "users"

    github_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    login: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    team_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    team: Mapped["Team"] = relationship("Team", back_populates="users")
    github_credential: Mapped["GitHubCredential | None"] = relationship(
        "GitHubCredential",
        back_populates="user",
        uselist=False,
    )

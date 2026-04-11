"""Team, membership, and API key models."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import BaseModel

if TYPE_CHECKING:
    from models.costs import CloudCostRecommendation
    from models.repositories import Repository


class SoftDeleteMixin:
    """Nullable deleted_at for soft deletes."""

    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Team(BaseModel, SoftDeleteMixin):
    """Organization using Auditr."""

    __tablename__ = "teams"

    name: Mapped[str] = mapped_column(String(255), nullable=False)

    members: Mapped[list["TeamMember"]] = relationship(
        back_populates="team",
        cascade="all, delete-orphan",
    )
    api_keys: Mapped[list["TeamAPIKey"]] = relationship(
        back_populates="team",
        cascade="all, delete-orphan",
    )
    repositories: Mapped[list["Repository"]] = relationship(
        back_populates="team",
        cascade="all, delete-orphan",
    )
    cost_recommendations: Mapped[list["CloudCostRecommendation"]] = relationship(
        back_populates="team",
        cascade="all, delete-orphan",
    )


class TeamMember(BaseModel, SoftDeleteMixin):
    """A user belonging to a team."""

    __tablename__ = "team_members"
    __table_args__ = (UniqueConstraint("team_id", "email", name="uq_team_members_team_email"),)

    team_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    github_login: Mapped[str | None] = mapped_column(String(100), nullable=True)
    role: Mapped[str] = mapped_column(String(32), nullable=False, default="member")

    team: Mapped["Team"] = relationship(back_populates="members")


class TeamAPIKey(BaseModel, SoftDeleteMixin):
    """Hashed API key for programmatic team access."""

    __tablename__ = "team_api_keys"

    team_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    key_prefix: Mapped[str] = mapped_column(String(16), nullable=False)
    key_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    scopes: Mapped[str | None] = mapped_column(Text, nullable=True)

    team: Mapped["Team"] = relationship(back_populates="api_keys")

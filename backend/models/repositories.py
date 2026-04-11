"""Repository and per-repo configuration."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import BaseModel
from models.teams import SoftDeleteMixin, Team

if TYPE_CHECKING:
    from models.builds import Build
    from models.code_clones import CodeClone
    from models.code_embeddings import CodeEmbedding
    from models.documentation import GeneratedDocumentation
    from models.pr_reviews import PRReview
    from models.vulnerabilities import VulnerabilityAlert


class Repository(BaseModel, SoftDeleteMixin):
    """Connected GitHub repository."""

    __tablename__ = "repositories"
    __table_args__ = (UniqueConstraint("github_repo_id", name="uq_repositories_github_repo_id"),)

    team_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    github_repo_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    default_branch: Mapped[str] = mapped_column(String(100), nullable=False, default="main")
    webhook_secret: Mapped[str | None] = mapped_column(String(255), nullable=True)
    github_hook_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    last_indexed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    team: Mapped["Team"] = relationship(back_populates="repositories")
    config: Mapped["RepositoryConfig | None"] = relationship(
        back_populates="repository",
        uselist=False,
        cascade="all, delete-orphan",
    )
    code_embeddings: Mapped[list["CodeEmbedding"]] = relationship(
        back_populates="repository",
        cascade="all, delete-orphan",
    )
    pr_reviews: Mapped[list["PRReview"]] = relationship(
        back_populates="repository",
        cascade="all, delete-orphan",
    )
    builds: Mapped[list["Build"]] = relationship(
        back_populates="repository",
        cascade="all, delete-orphan",
    )
    vulnerability_alerts: Mapped[list["VulnerabilityAlert"]] = relationship(
        back_populates="repository",
        cascade="all, delete-orphan",
    )
    code_clones: Mapped[list["CodeClone"]] = relationship(
        back_populates="repository",
        cascade="all, delete-orphan",
    )
    generated_documentation: Mapped[list["GeneratedDocumentation"]] = relationship(
        back_populates="repository",
        cascade="all, delete-orphan",
    )


class RepositoryConfig(BaseModel, SoftDeleteMixin):
    """Flexible JSON settings for indexing, webhooks, and feature flags."""

    __tablename__ = "repository_configs"
    __table_args__ = (UniqueConstraint("repository_id", name="uq_repository_configs_repository_id"),)

    repository_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("repositories.id", ondelete="CASCADE"),
        nullable=False,
    )
    settings: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    repository: Mapped["Repository"] = relationship(back_populates="config")

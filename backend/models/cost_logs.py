"""LLM API cost audit rows (no secrets)."""

from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import BigInteger, ForeignKey, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from database import BaseModel


class CostLog(BaseModel):
    """One billed LLM or embedding call."""

    __tablename__ = "cost_logs"

    tokens_used: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    cost_in_usd: Mapped[Decimal] = mapped_column(Numeric(14, 6), nullable=False, default=Decimal("0"))
    model: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    feature: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    repo_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("repositories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    team_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("teams.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

"""Cloud cost optimization recommendations."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import BaseModel
from models.teams import SoftDeleteMixin, Team

if TYPE_CHECKING:
    pass


class CloudCostRecommendation(BaseModel, SoftDeleteMixin):
    """ML/rule-based savings opportunity for a cloud resource."""

    __tablename__ = "cloud_cost_recommendations"

    team_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider: Mapped[str | None] = mapped_column(String(50), nullable=True)
    resource_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    resource_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    current_cost_monthly: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    potential_saving: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    recommendation: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="open")
    cost_data: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    detected_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    team: Mapped["Team"] = relationship(back_populates="cost_recommendations")

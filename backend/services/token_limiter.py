"""Per-team monthly token budget with Redis counters and graceful degradation."""

from __future__ import annotations

import calendar
import datetime
import logging
import uuid
from datetime import UTC
from typing import Literal

import redis.asyncio as redis

from config import get_settings
from config.llm_config import get_llm_config

logger = logging.getLogger(__name__)

FeatureTier = Literal["cheap", "expensive"]


EXPENSIVE_FEATURES = frozenset(
    {
        "code_review",
        "sql_optimization",
        "vulnerability_triage",
        "documentation",
    },
)


def _month_key(when: datetime.datetime | None = None) -> str:
    dt = when or datetime.datetime.now(UTC)
    return f"{dt.year:04d}{dt.month:02d}"


def _budget_key(team_id: uuid.UUID, month: str) -> str:
    return f"team:{team_id}:tokens:{month}"


class TeamTokenLimiter:
    """Track monthly token usage per team; warn near limit; block expensive features when over."""

    def __init__(self, redis_url: str | None = None) -> None:
        settings = get_settings()
        self._url = redis_url or settings.redis_url
        self._client: redis.Redis | None = None

    async def _get_client(self) -> redis.Redis:
        if self._client is None:
            self._client = redis.from_url(self._url, decode_responses=True)
        return self._client

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    def monthly_budget_for_team(self, _team_id: uuid.UUID) -> int:
        """0 means unlimited."""
        return get_llm_config().default_monthly_team_token_budget

    async def record_tokens(self, team_id: uuid.UUID, tokens: int) -> int:
        """Add tokens for current month; returns new cumulative total."""
        if tokens <= 0:
            return await self.current_month_usage(team_id)
        r = await self._get_client()
        key = _budget_key(team_id, _month_key())
        n = await r.incrby(key, tokens)
        now = datetime.datetime.now(UTC)
        _, days = calendar.monthrange(now.year, now.month)
        ttl = days * 86400 * 2
        await r.expire(key, ttl)
        await self._maybe_warn(team_id, int(n))
        return int(n)

    async def current_month_usage(self, team_id: uuid.UUID) -> int:
        r = await self._get_client()
        key = _budget_key(team_id, _month_key())
        v = await r.get(key)
        return int(v) if v else 0

    async def _maybe_warn(self, team_id: uuid.UUID, usage: int) -> None:
        budget = self.monthly_budget_for_team(team_id)
        if budget <= 0:
            return
        ratio = usage / budget
        warn_at = get_llm_config().warn_budget_ratio
        if ratio >= warn_at:
            logger.warning(
                "team_token_budget_warning",
                extra={
                    "team_id": str(team_id),
                    "usage": usage,
                    "budget": budget,
                    "ratio": round(ratio, 3),
                    "action_taken": "budget_warn",
                },
            )

    async def is_over_budget(self, team_id: uuid.UUID) -> bool:
        budget = self.monthly_budget_for_team(team_id)
        if budget <= 0:
            return False
        use = await self.current_month_usage(team_id)
        return use >= budget

    def feature_tier(self, feature: str) -> FeatureTier:
        return "expensive" if feature in EXPENSIVE_FEATURES else "cheap"

    async def is_feature_allowed(self, team_id: uuid.UUID | None, feature: str) -> bool:
        """Cheap features may still run when over budget; expensive ones are disabled."""
        if team_id is None:
            return True
        if not await self.is_over_budget(team_id):
            return True
        return self.feature_tier(feature) == "cheap"

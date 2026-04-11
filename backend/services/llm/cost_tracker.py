"""Persist LLM cost rows and aggregate dashboard queries."""

from __future__ import annotations

import logging
import uuid
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.cost_logs import CostLog

logger = logging.getLogger(__name__)

# USD per 1M tokens (input / output) — approximate; update as provider pricing changes.
_MODEL_RATES: dict[str, tuple[Decimal, Decimal]] = {
    "gpt-4o": (Decimal("2.50"), Decimal("10.00")),
    "gpt-4o-mini": (Decimal("0.15"), Decimal("0.60")),
    "claude-sonnet-4-20250514": (Decimal("3.00"), Decimal("15.00")),
    "text-embedding-3-small": (Decimal("0.02"), Decimal("0.00")),
}


def _rates_for_model(model: str) -> tuple[Decimal, Decimal]:
    m = model.lower()
    for key, rates in _MODEL_RATES.items():
        if key in m:
            return rates
    # Default heuristic
    return Decimal("3.00"), Decimal("15.00")


def estimate_cost_usd(input_tokens: int, output_tokens: int, model: str) -> Decimal:
    """Compute USD cost from token usage (OpenAI-style split; embeddings use input only)."""
    inp_rate, out_rate = _rates_for_model(model)
    inp = Decimal(input_tokens) * inp_rate / Decimal(1_000_000)
    out = Decimal(output_tokens) * out_rate / Decimal(1_000_000)
    return (inp + out).quantize(Decimal("0.000001"))


async def log_llm_cost(
    session: AsyncSession,
    *,
    tokens_used: int,
    model: str,
    feature: str,
    input_tokens: int,
    output_tokens: int,
    repo_id: uuid.UUID | None = None,
    team_id: uuid.UUID | None = None,
    cached: bool = False,
) -> CostLog:
    """
    Insert a cost log row. Skips billing when cached=True (no provider charge).

    Never logs secrets — only metadata and aggregates.
    """
    if cached:
        cost = Decimal("0")
        tok = 0
    else:
        cost = estimate_cost_usd(input_tokens, output_tokens, model)
        tok = tokens_used if tokens_used else (input_tokens + output_tokens)

    row = CostLog(
        tokens_used=tok,
        cost_in_usd=cost,
        model=model,
        feature=feature,
        repo_id=repo_id,
        team_id=team_id,
    )
    session.add(row)
    await session.flush()
    logger.info(
        "llm_cost_logged",
        extra={
            "model": model,
            "feature": feature,
            "tokens_used": tok,
            "cost_in_usd": float(cost),
            "repo_id": str(repo_id) if repo_id else None,
            "team_id": str(team_id) if team_id else None,
            "cached": cached,
            "action_taken": "cost_log_insert",
        },
    )
    return row


async def total_spend(session: AsyncSession, *, team_id: uuid.UUID | None = None) -> Decimal:
    q = select(func.coalesce(func.sum(CostLog.cost_in_usd), 0))
    if team_id is not None:
        q = q.where(CostLog.team_id == team_id)
    res = await session.execute(q)
    val = res.scalar_one()
    return Decimal(val or 0)


async def cost_by_feature(
    session: AsyncSession,
    *,
    team_id: uuid.UUID | None = None,
) -> list[dict[str, Any]]:
    q = select(CostLog.feature, func.sum(CostLog.cost_in_usd)).group_by(CostLog.feature)
    if team_id is not None:
        q = q.where(CostLog.team_id == team_id)
    res = await session.execute(q)
    rows = res.all()
    return [{"feature": r[0], "cost_in_usd": float(r[1] or 0)} for r in rows]


async def cost_by_repo(
    session: AsyncSession,
    *,
    team_id: uuid.UUID | None = None,
) -> list[dict[str, Any]]:
    q = select(CostLog.repo_id, func.sum(CostLog.cost_in_usd)).group_by(CostLog.repo_id)
    q = q.where(CostLog.repo_id.is_not(None))
    if team_id is not None:
        q = q.where(CostLog.team_id == team_id)
    res = await session.execute(q)
    rows = res.all()
    return [{"repo_id": str(r[0]), "cost_in_usd": float(r[1] or 0)} for r in rows if r[0]]

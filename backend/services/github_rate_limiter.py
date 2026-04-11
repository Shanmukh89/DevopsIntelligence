"""Track GitHub REST rate limits, backoff, and Celery retry scheduling."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any

import httpx

from celery_app import celery_app

logger = logging.getLogger(__name__)

_WARN_REMAINING = 50


@dataclass
class RateLimitSnapshot:
    limit: int | None = None
    remaining: int | None = None
    reset_epoch: float | None = None
    resource: str | None = None
    last_updated: float = field(default_factory=time.time)


_snapshot = RateLimitSnapshot()


def update_from_response(response: httpx.Response) -> None:
    """Parse GitHub rate limit headers after each API response."""
    global _snapshot
    try:
        lim = response.headers.get("X-RateLimit-Limit")
        rem = response.headers.get("X-RateLimit-Remaining")
        rst = response.headers.get("X-RateLimit-Reset")
        res = response.headers.get("X-RateLimit-Resource")
        if lim is not None:
            _snapshot.limit = int(lim)
        if rem is not None:
            _snapshot.remaining = int(rem)
        if rst is not None:
            _snapshot.reset_epoch = float(rst)
        if res:
            _snapshot.resource = res
        _snapshot.last_updated = time.time()
    except (TypeError, ValueError):
        return

    if _snapshot.remaining is not None and _snapshot.remaining < _WARN_REMAINING:
        logger.warning(
            "github_rate_limit_low",
            extra={
                "remaining": _snapshot.remaining,
                "limit": _snapshot.limit,
                "resource": _snapshot.resource,
            },
        )


def snapshot() -> RateLimitSnapshot:
    return _snapshot


def should_preemptive_slow_down() -> bool | float:
    """
    If close to limit, return suggested sleep seconds before next call; else False.
    """
    if _snapshot.remaining is None:
        return False
    if _snapshot.remaining <= 0 and _snapshot.reset_epoch:
        wait = max(0.0, _snapshot.reset_epoch - time.time())
        return max(wait, 1.0)
    if _snapshot.remaining < 10:
        return 1.0
    return False


@celery_app.task(name="github.retry_http_task", bind=True)
def retry_http_task(self, task_name: str, args: list[Any], kwargs: dict[str, Any], countdown: int) -> str:
    """Re-dispatch another Celery task after rate-limit backoff."""
    logger.info(
        "github_retry_scheduled",
        extra={"task": task_name, "countdown": countdown, "celery_id": self.request.id},
    )
    celery_app.send_task(task_name, args=args, kwargs=kwargs, countdown=countdown)
    return f"scheduled:{task_name}"


def schedule_rate_limited_retry(
    task_name: str,
    *,
    args: list[Any] | None = None,
    kwargs: dict[str, Any] | None = None,
    response: httpx.Response | None = None,
) -> None:
    """Queue a retry on the generic retry task with exponential-ish delay."""
    delay = 60
    if response is not None:
        ra = response.headers.get("Retry-After")
        if ra and ra.isdigit():
            delay = int(ra)
        else:
            reset = response.headers.get("X-RateLimit-Reset")
            if reset and reset.isdigit():
                delay = max(int(float(reset) - time.time()), 1)
    retry_http_task.delay(task_name, args or [], kwargs or {}, delay)


def compute_backoff_seconds(attempt: int, *, base: float = 1.0, cap: float = 60.0) -> float:
    return min(cap, base * (2**attempt))

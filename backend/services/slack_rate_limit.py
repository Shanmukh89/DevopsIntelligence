"""Per-channel Slack rate tracking and 429 backoff helpers."""

from __future__ import annotations

import asyncio
import time
from collections import defaultdict
from dataclasses import dataclass, field


@dataclass
class ChannelRateState:
    """Rolling window message counts per channel."""

    window_start: float = field(default_factory=time.monotonic)
    count: int = 0


class SlackChannelRateLimiter:
    """
    Track approximate posts per channel per minute (Slack tier limits vary).
    Used to batch/coalesce before hitting API limits.
    """

    def __init__(self, *, max_per_minute: int = 50) -> None:
        self._max = max_per_minute
        self._lock = asyncio.Lock()
        self._channels: dict[str, ChannelRateState] = defaultdict(ChannelRateState)

    async def should_delay(self, channel_id: str) -> float:
        """Return seconds to wait before sending (0 if ok)."""
        async with self._lock:
            now = time.monotonic()
            st = self._channels[channel_id]
            if now - st.window_start > 60.0:
                st.window_start = now
                st.count = 0
            if st.count >= self._max:
                return max(0.0, 60.0 - (now - st.window_start))
            st.count += 1
            return 0.0

    async def record_429(self, channel_id: str) -> None:
        """After a 429, treat channel as hot — reduce effective budget."""
        async with self._lock:
            st = self._channels[channel_id]
            st.count = self._max


def compute_backoff_seconds(attempt: int, retry_after: float | None) -> float:
    """Exponential backoff with optional Retry-After from Slack."""
    if retry_after is not None:
        return float(retry_after)
    base = min(2**attempt, 120)
    return float(base)

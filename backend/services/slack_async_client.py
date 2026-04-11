"""Async Slack Web API via httpx with 429 backoff (never log tokens)."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

from services.slack_rate_limit import SlackChannelRateLimiter, compute_backoff_seconds

logger = logging.getLogger(__name__)

SLACK_API = "https://slack.com/api"


class AsyncSlackClient:
    """Post/update Slack messages with exponential backoff on HTTP 429."""

    def __init__(
        self,
        *,
        rate_limiter: SlackChannelRateLimiter | None = None,
        max_retries: int = 5,
    ) -> None:
        self._rate_limiter = rate_limiter or SlackChannelRateLimiter()
        self._max_retries = max_retries

    async def _post_api(
        self,
        token: str,
        rate_bucket: str,
        method: str,
        json_body: dict[str, Any],
    ) -> dict[str, Any]:
        delay = await self._rate_limiter.should_delay(rate_bucket)
        if delay > 0:
            await asyncio.sleep(delay)

        url = f"{SLACK_API}/{method}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8",
        }
        attempt = 0
        async with httpx.AsyncClient(timeout=60.0) as client:
            while attempt < self._max_retries:
                resp = await client.post(url, headers=headers, json=json_body)
                if resp.status_code == 429:
                    await self._rate_limiter.record_429(rate_bucket)
                    ra = resp.headers.get("Retry-After")
                    try:
                        retry_after = float(ra) if ra else None
                    except ValueError:
                        retry_after = None
                    wait = compute_backoff_seconds(attempt, retry_after)
                    logger.warning("slack_429 method=%s retry_in=%ss", method, wait)
                    await asyncio.sleep(wait)
                    attempt += 1
                    continue
                try:
                    data = resp.json()
                except Exception:
                    logger.warning("slack_bad_json method=%s status=%s", method, resp.status_code)
                    return {"ok": False, "error": "invalid_json"}
                if not data.get("ok") and data.get("error") == "ratelimited":
                    wait = compute_backoff_seconds(attempt, None)
                    logger.warning("slack_ratelimited method=%s retry_in=%ss", method, wait)
                    await asyncio.sleep(wait)
                    attempt += 1
                    continue
                return data
        return {"ok": False, "error": "max_retries"}

    async def chat_post_message(self, token: str, channel: str, **fields: Any) -> dict[str, Any]:
        body: dict[str, Any] = {"channel": channel, **fields}
        return await self._post_api(token, channel, "chat.postMessage", body)

    async def chat_update(self, token: str, channel: str, ts: str, **fields: Any) -> dict[str, Any]:
        body: dict[str, Any] = {"channel": channel, "ts": ts, **fields}
        return await self._post_api(token, channel, "chat.update", body)

    async def conversations_list(self, token: str, **params: Any) -> dict[str, Any]:
        # Form-encoded for slack API list methods
        delay = await self._rate_limiter.should_delay("conversations.list")
        if delay > 0:
            await asyncio.sleep(delay)
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        attempt = 0
        async with httpx.AsyncClient(timeout=60.0) as client:
            while attempt < self._max_retries:
                resp = await client.post(
                    f"{SLACK_API}/conversations.list",
                    headers=headers,
                    data=params,
                )
                if resp.status_code == 429:
                    await self._rate_limiter.record_429("conversations.list")
                    ra = resp.headers.get("Retry-After")
                    try:
                        retry_after = float(ra) if ra else None
                    except ValueError:
                        retry_after = None
                    wait = compute_backoff_seconds(attempt, retry_after)
                    await asyncio.sleep(wait)
                    attempt += 1
                    continue
                try:
                    return resp.json()
                except Exception:
                    return {"ok": False, "error": "invalid_json"}
        return {"ok": False, "error": "max_retries"}

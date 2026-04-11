"""Redis-backed LLM response cache."""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any, Literal

import redis.asyncio as redis

from config import get_settings

logger = logging.getLogger(__name__)

TTL_CODE_ANALYSIS_SECONDS = 7 * 24 * 60 * 60  # 7 days
TTL_REALTIME_SECONDS = 60 * 60  # 1 hour

CacheKind = Literal["analysis", "realtime"]


def cache_key_digest(model: str, messages: list[dict[str, Any]], temperature: float) -> str:
    """Stable SHA-256 over model + serialized messages + temperature."""
    payload = json.dumps(
        {"model": model, "messages": messages, "temperature": temperature},
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _response_key(digest: str) -> str:
    return f"llm:resp:{digest}"


def _repo_index_key(repo_id: str) -> str:
    return f"llm:repo:{repo_id}:keys"


class LLMCache:
    """Redis get/set for LLM completions with optional repo-scoped purge."""

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

    def ttl_for_kind(self, kind: CacheKind) -> int:
        return TTL_CODE_ANALYSIS_SECONDS if kind == "analysis" else TTL_REALTIME_SECONDS

    async def get_cached_response(self, key_digest: str) -> str | None:
        """Return cached text or None."""
        try:
            r = await self._get_client()
            val = await r.get(_response_key(key_digest))
            if val is None:
                return None
            return str(val)
        except redis.RedisError as e:
            logger.warning("llm_cache_get_failed", extra={"error_type": type(e).__name__})
            return None

    async def set_cached_response(
        self,
        key_digest: str,
        response: str,
        ttl: int,
        *,
        repo_id: str | None = None,
    ) -> None:
        try:
            r = await self._get_client()
            k = _response_key(key_digest)
            await r.set(k, response, ex=ttl)
            if repo_id:
                await r.sadd(_repo_index_key(repo_id), key_digest)
                await r.expire(_repo_index_key(repo_id), ttl)
        except redis.RedisError as e:
            logger.warning("llm_cache_set_failed", extra={"error_type": type(e).__name__})

    async def clear_cache_for_repo(self, repo_id: str) -> int:
        """Delete all cached LLM entries indexed for this repository. Returns deleted key count."""
        deleted = 0
        try:
            r = await self._get_client()
            idx = _repo_index_key(repo_id)
            members = await r.smembers(idx)
            for digest in members or []:
                dk = _response_key(str(digest))
                n = await r.delete(dk)
                deleted += int(n)
            await r.delete(idx)
        except redis.RedisError as e:
            logger.warning("llm_cache_clear_failed", extra={"error_type": type(e).__name__})
        return deleted

    async def get_json(self, key: str) -> str | None:
        """Read a JSON-serializable string payload (e.g. embedding cache)."""
        try:
            r = await self._get_client()
            return await r.get(key)
        except redis.RedisError as e:
            logger.warning("cache_get_json_failed", extra={"error_type": type(e).__name__})
            return None

    async def set_json(self, key: str, payload: str, ttl: int) -> None:
        """Store a string payload with TTL."""
        try:
            r = await self._get_client()
            await r.set(key, payload, ex=ttl)
        except redis.RedisError as e:
            logger.warning("cache_set_json_failed", extra={"error_type": type(e).__name__})

"""Multi-provider async LLM client with fallback, streaming, timeouts, and optional cache."""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any, Literal

import httpx

from config.llm_config import fallback_chain_for_model, get_llm_config, model_provider
from services.llm.caching import LLMCache, cache_key_digest
from services.llm.token_estimate import (
    default_max_context_tokens,
    estimate_messages_tokens,
    truncate_messages_to_budget,
)

logger = logging.getLogger(__name__)

OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"
ANTHROPIC_MESSAGES_URL = "https://api.anthropic.com/v1/messages"


@dataclass
class LLMCallResult:
    """Non-streaming completion with usage metadata for cost tracking."""

    text: str
    model_used: str
    provider: Literal["openai", "anthropic"]
    input_tokens: int
    output_tokens: int
    raw_usage: dict[str, Any]


class LLMClient:
    """
    Unified client for OpenAI and Anthropic chat models.

    - 30s timeout on HTTP calls
    - Primary model with automatic fallback to the other provider on failure
    - Optional Redis cache (same prompt → cached body)
    """

    def __init__(
        self,
        *,
        http_client: httpx.AsyncClient | None = None,
        cache: LLMCache | None = None,
        config: Any | None = None,
    ) -> None:
        self._config = config or get_llm_config()
        self._cache = cache or LLMCache()
        self._own_client = http_client is None
        timeout = httpx.Timeout(self._config.request_timeout_seconds)
        self._http = http_client or httpx.AsyncClient(timeout=timeout)

    async def aclose(self) -> None:
        if self._own_client:
            await self._http.aclose()
        await self._cache.close()

    async def call_llm(
        self,
        model: str,
        messages: list[dict[str, Any]],
        *,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        use_cache: bool = True,
        cache_kind: Literal["analysis", "realtime"] = "analysis",
        repo_id: str | None = None,
    ) -> LLMCallResult:
        """
        Run a chat completion with provider fallback.

        Token estimation trims input so the request stays within model context minus max_tokens output.
        """
        prepared = self._prepare_messages(model, messages, max_tokens)
        digest = cache_key_digest(model, prepared, temperature)
        if use_cache:
            cached = await self._cache.get_cached_response(digest)
            if cached is not None:
                return LLMCallResult(
                    text=cached,
                    model_used=model,
                    provider=model_provider(model),
                    input_tokens=0,
                    output_tokens=0,
                    raw_usage={"cached": True},
                )

        last_error: Exception | None = None
        for attempt_model in fallback_chain_for_model(model):
            try:
                if model_provider(attempt_model) == "openai":
                    result = await self._call_openai(attempt_model, prepared, temperature, max_tokens)
                else:
                    result = await self._call_anthropic(attempt_model, prepared, temperature, max_tokens)
                if use_cache:
                    ttl = self._cache.ttl_for_kind(cache_kind)
                    await self._cache.set_cached_response(
                        digest,
                        result.text,
                        ttl,
                        repo_id=repo_id,
                    )
                return result
            except Exception as e:
                last_error = e
                logger.warning(
                    "llm_provider_attempt_failed",
                    extra={
                        "model": attempt_model,
                        "error_type": type(e).__name__,
                        "action_taken": "fallback",
                    },
                )
        assert last_error is not None
        raise last_error

    def _prepare_messages(
        self,
        model: str,
        messages: list[dict[str, Any]],
        max_tokens: int,
    ) -> list[dict[str, Any]]:
        ctx = default_max_context_tokens(model)
        return truncate_messages_to_budget(
            messages,
            model,
            ctx,
            reserve_output_tokens=max_tokens,
        )

    async def stream_llm(
        self,
        model: str,
        messages: list[dict[str, Any]],
        *,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> AsyncIterator[str]:
        """Yield text fragments as they arrive (streaming). Not cached."""
        prepared = self._prepare_messages(model, messages, max_tokens)
        last_error: Exception | None = None
        for attempt_model in fallback_chain_for_model(model):
            try:
                if model_provider(attempt_model) == "openai":
                    async for chunk in self._stream_openai(attempt_model, prepared, temperature, max_tokens):
                        yield chunk
                    return
                async for chunk in self._stream_anthropic(attempt_model, prepared, temperature, max_tokens):
                    yield chunk
                return
            except Exception as e:
                last_error = e
                logger.warning(
                    "llm_stream_attempt_failed",
                    extra={"model": attempt_model, "error_type": type(e).__name__},
                )
        assert last_error is not None
        raise last_error

    async def _call_openai(
        self,
        model: str,
        messages: list[dict[str, Any]],
        temperature: float,
        max_tokens: int,
    ) -> LLMCallResult:
        key = self._config.openai_api_key
        if not key:
            msg = "OPENAI_API_KEY is not configured"
            raise RuntimeError(msg)
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }
        body: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        r = await self._http.post(OPENAI_CHAT_URL, headers=headers, json=body)
        r.raise_for_status()
        data = r.json()
        choice = data["choices"][0]
        text = choice.get("message", {}).get("content") or ""
        usage = data.get("usage") or {}
        inp = int(usage.get("prompt_tokens", 0))
        out = int(usage.get("completion_tokens", 0))
        return LLMCallResult(
            text=text,
            model_used=model,
            provider="openai",
            input_tokens=inp,
            output_tokens=out,
            raw_usage=usage,
        )

    async def _call_anthropic(
        self,
        model: str,
        messages: list[dict[str, Any]],
        temperature: float,
        max_tokens: int,
    ) -> LLMCallResult:
        key = self._config.anthropic_api_key
        if not key:
            msg = "ANTHROPIC_API_KEY is not configured"
            raise RuntimeError(msg)
        system, anth_msgs = self._anthropic_messages(messages)
        headers = {
            "x-api-key": key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        body: dict[str, Any] = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": anth_msgs,
        }
        if system:
            body["system"] = system
        r = await self._http.post(ANTHROPIC_MESSAGES_URL, headers=headers, json=body)
        r.raise_for_status()
        data = r.json()
        text = self._anthropic_text_from_content(data.get("content", []))
        usage = data.get("usage") or {}
        inp = int(usage.get("input_tokens", 0))
        out = int(usage.get("output_tokens", 0))
        return LLMCallResult(
            text=text,
            model_used=model,
            provider="anthropic",
            input_tokens=inp,
            output_tokens=out,
            raw_usage=usage,
        )

    @staticmethod
    def _anthropic_messages(
        messages: list[dict[str, Any]],
    ) -> tuple[str, list[dict[str, Any]]]:
        system_parts: list[str] = []
        out: list[dict[str, Any]] = []
        for m in messages:
            role = m.get("role", "user")
            content = m.get("content", "")
            if role == "system":
                system_parts.append(str(content))
                continue
            ar = "assistant" if role == "assistant" else "user"
            out.append({"role": ar, "content": content})
        return "\n\n".join(system_parts), out

    @staticmethod
    def _anthropic_text_from_content(blocks: list[dict[str, Any]]) -> str:
        parts: list[str] = []
        for b in blocks:
            if b.get("type") == "text":
                parts.append(str(b.get("text", "")))
        return "".join(parts)

    async def _stream_openai(
        self,
        model: str,
        messages: list[dict[str, Any]],
        temperature: float,
        max_tokens: int,
    ) -> AsyncIterator[str]:
        key = self._config.openai_api_key
        if not key:
            msg = "OPENAI_API_KEY is not configured"
            raise RuntimeError(msg)
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }
        async with self._http.stream("POST", OPENAI_CHAT_URL, headers=headers, json=body) as r:
            r.raise_for_status()
            async for line in r.aiter_lines():
                if not line or not line.startswith("data: "):
                    continue
                data = line[6:]
                if data.strip() == "[DONE]":
                    break
                try:
                    chunk = json.loads(data)
                    delta = chunk["choices"][0].get("delta", {})
                    piece = delta.get("content")
                    if piece:
                        yield piece
                except (json.JSONDecodeError, KeyError, IndexError):
                    continue

    async def _stream_anthropic(
        self,
        model: str,
        messages: list[dict[str, Any]],
        temperature: float,
        max_tokens: int,
    ) -> AsyncIterator[str]:
        key = self._config.anthropic_api_key
        if not key:
            msg = "ANTHROPIC_API_KEY is not configured"
            raise RuntimeError(msg)
        system, anth_msgs = self._anthropic_messages(messages)
        headers = {
            "x-api-key": key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        body: dict[str, Any] = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": anth_msgs,
            "stream": True,
        }
        if system:
            body["system"] = system
        async with self._http.stream("POST", ANTHROPIC_MESSAGES_URL, headers=headers, json=body) as r:
            r.raise_for_status()
            async for line in r.aiter_lines():
                if not line or not line.startswith("data: "):
                    continue
                payload = line[6:]
                try:
                    ev = json.loads(payload)
                except json.JSONDecodeError:
                    continue
                if ev.get("type") == "content_block_delta":
                    delta = ev.get("delta", {})
                    if delta.get("type") == "text_delta":
                        t = delta.get("text")
                        if t:
                            yield t

    def estimate_input_tokens(self, model: str, messages: list[dict[str, Any]]) -> int:
        """Public helper for pre-flight checks."""
        return estimate_messages_tokens(messages, model)

"""Embedding providers (OpenAI API + optional local sentence-transformers) with Redis caching."""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
from typing import Literal

import httpx

from config import get_settings
from config.llm_config import get_llm_config
from services.llm.caching import LLMCache

logger = logging.getLogger(__name__)

OPENAI_EMBEDDINGS_URL = "https://api.openai.com/v1/embeddings"
EmbeddingBackend = Literal["openai", "hf"]


def _embed_cache_key(text: str, model: str) -> str:
    raw = f"{model}|{text}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _redis_key(digest: str) -> str:
    return f"embed:vec:{digest}"


def _run_hf_encode(texts: list[str], model_name: str) -> list[list[float]]:
    from sentence_transformers import SentenceTransformer

    st = SentenceTransformer(model_name)
    emb = st.encode(texts, convert_to_numpy=True)
    return [emb[i].tolist() for i in range(len(texts))]


class EmbeddingService:
    """Async embeddings with optional Redis vector cache."""

    def __init__(
        self,
        *,
        http_client: httpx.AsyncClient | None = None,
        cache: LLMCache | None = None,
    ) -> None:
        self._cfg = get_llm_config()
        self._settings = get_settings()
        self._cache = cache or LLMCache()
        self._own_client = http_client is None
        timeout = httpx.Timeout(self._cfg.request_timeout_seconds)
        self._http = http_client or httpx.AsyncClient(timeout=timeout)

    async def aclose(self) -> None:
        if self._own_client:
            await self._http.aclose()
        await self._cache.close()

    async def embed_text(
        self,
        text: str,
        model: EmbeddingBackend = "openai",
        *,
        use_cache: bool = True,
    ) -> list[float]:
        vecs = await self.batch_embed([text], model, use_cache=use_cache)
        return vecs[0]

    async def batch_embed(
        self,
        texts: list[str],
        model: EmbeddingBackend = "openai",
        *,
        use_cache: bool = True,
    ) -> list[list[float]]:
        if not texts:
            return []
        if model == "openai":
            return await self._batch_openai(texts, use_cache=use_cache)
        if model == "hf":
            return await self._batch_hf(texts, use_cache=use_cache)
        msg = f"Unknown embedding backend: {model}"
        raise ValueError(msg)

    async def _batch_openai(self, texts: list[str], *, use_cache: bool) -> list[list[float]]:
        cfg = self._cfg
        key = self._settings.openai_api_key
        if not key:
            msg = "OPENAI_API_KEY is not configured"
            raise RuntimeError(msg)
        out: list[list[float] | None] = [None] * len(texts)
        pending_idx: list[int] = []
        pending_texts: list[str] = []

        for i, t in enumerate(texts):
            digest = _embed_cache_key(t, cfg.embedding_openai_model)
            if use_cache:
                cached = await self._get_cached_vector(digest)
                if cached is not None:
                    out[i] = cached
                    continue
            pending_idx.append(i)
            pending_texts.append(t)

        if pending_texts:
            headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
            body = {"model": cfg.embedding_openai_model, "input": pending_texts}
            r = await self._http.post(OPENAI_EMBEDDINGS_URL, headers=headers, json=body)
            r.raise_for_status()
            data = r.json()
            for j, item in enumerate(data.get("data", [])):
                vec = item.get("embedding")
                if not isinstance(vec, list):
                    continue
                orig_i = pending_idx[j]
                out[orig_i] = [float(x) for x in vec]
                if use_cache:
                    d = _embed_cache_key(texts[orig_i], cfg.embedding_openai_model)
                    await self._set_cached_vector(d, out[orig_i])

        resolved: list[list[float]] = []
        for v in out:
            if v is None:
                msg = "embedding_missing"
                raise RuntimeError(msg)
            resolved.append(v)
        return resolved

    async def _get_cached_vector(self, digest: str) -> list[float] | None:
        raw = await self._cache.get_json(_redis_key(digest))
        if not raw:
            return None
        try:
            data = json.loads(raw)
            if isinstance(data, list):
                return [float(x) for x in data]
        except (json.JSONDecodeError, TypeError, ValueError) as e:
            logger.debug("embed_cache_decode_failed", extra={"reason": str(e)})
        return None

    async def _set_cached_vector(self, digest: str, vector: list[float]) -> None:
        ttl = self._cache.ttl_for_kind("analysis")
        await self._cache.set_json(_redis_key(digest), json.dumps(vector), ttl)

    async def _batch_hf(self, texts: list[str], *, use_cache: bool) -> list[list[float]]:
        cfg = self._cfg
        mname = cfg.embedding_hf_model
        out: list[list[float] | None] = [None] * len(texts)
        pending_idx: list[int] = []
        pending_texts: list[str] = []

        for i, t in enumerate(texts):
            digest = _embed_cache_key(t, f"hf:{mname}")
            if use_cache:
                cached = await self._get_cached_vector(digest)
                if cached is not None:
                    out[i] = cached
                    continue
            pending_idx.append(i)
            pending_texts.append(t)

        if pending_texts:
            vecs = await asyncio.to_thread(_run_hf_encode, pending_texts, mname)
            for j, idx in enumerate(pending_idx):
                out[idx] = vecs[j]
                if use_cache:
                    d = _embed_cache_key(texts[idx], f"hf:{mname}")
                    await self._set_cached_vector(d, vecs[j])

        resolved: list[list[float]] = []
        for v in out:
            if v is None:
                msg = "hf_embedding_missing"
                raise RuntimeError(msg)
            resolved.append(v)
        return resolved

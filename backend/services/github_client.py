"""Async GitHub REST API client with Redis cache, rate limits, and retries."""

from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import logging
from collections.abc import Awaitable, Callable
from typing import Any
from urllib.parse import quote

import httpx
import redis.asyncio as redis
from redis.exceptions import RedisError

from config import BaseAppSettings
from services import github_rate_limiter
from services.github_pagination import fetch_all_pages_json

logger = logging.getLogger(__name__)

CACHE_TTL_SECONDS = 3600


def _split_repo(full_name: str) -> tuple[str, str]:
    parts = full_name.split("/", 1)
    if len(parts) != 2 or not parts[0] or not parts[1]:
        raise ValueError(f"Invalid repo full_name: {full_name!r}")
    return parts[0], parts[1]


class GitHubClient:
    """Async wrapper around GitHub REST API using httpx + optional Redis cache."""

    def __init__(
        self,
        settings: BaseAppSettings,
        token: str | None = None,
        *,
        redis_client: redis.Redis | None = None,
        on_unauthorized: Callable[[], Awaitable[str | None]] | None = None,
    ) -> None:
        self._settings = settings
        self._token = token
        self._base = "https://api.github.com"
        self._redis = redis_client
        self._on_unauthorized = on_unauthorized

    def _cache_key(self, method: str, path: str, params: dict[str, Any] | None) -> str:
        h = hashlib.sha256()
        h.update(method.encode())
        h.update(path.encode())
        h.update(json.dumps(params or {}, sort_keys=True).encode())
        if self._token:
            h.update(hashlib.sha256(self._token.encode()).digest())
        return f"gh:cache:{h.hexdigest()[:40]}"

    def _headers(self, extra: dict[str, str] | None = None) -> dict[str, str]:
        h: dict[str, str] = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self._token:
            h["Authorization"] = f"Bearer {self._token}"
        if extra:
            h.update(extra)
        return h

    async def _maybe_sleep_rate_limit(self) -> None:
        slow = github_rate_limiter.should_preemptive_slow_down()
        if slow:
            if isinstance(slow, float):
                await asyncio.sleep(min(slow, 60.0))
            else:
                await asyncio.sleep(1.0)

    async def _get_cached(self, cache_key: str) -> bytes | None:
        if not self._redis:
            return None
        try:
            return await self._redis.get(cache_key)
        except RedisError:
            return None

    async def _set_cached(self, cache_key: str, value: bytes) -> None:
        if not self._redis:
            return
        try:
            await self._redis.setex(cache_key, CACHE_TTL_SECONDS, value)
        except RedisError:
            pass

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: Any = None,
        headers_extra: dict[str, str] | None = None,
        max_retries: int = 4,
        use_cache: bool = True,
        follow_redirects: bool = True,
    ) -> httpx.Response:
        url = path if path.startswith("http") else f"{self._base}{path}"
        cache_key = self._cache_key(method, path, params)
        if method == "GET" and use_cache and json_body is None:
            raw = await self._get_cached(cache_key)
            if raw:
                return httpx.Response(200, content=raw, request=httpx.Request(method, url))

        await self._maybe_sleep_rate_limit()
        delay = 1.0
        last_exc: Exception | None = None
        unauthorized_retried = False
        async with httpx.AsyncClient(timeout=120.0) as client:
            for attempt in range(max_retries):
                try:
                    resp = await client.request(
                        method,
                        url,
                        headers=self._headers(headers_extra),
                        params=params,
                        json=json_body,
                        follow_redirects=follow_redirects,
                    )
                    github_rate_limiter.update_from_response(resp)

                    if resp.status_code == 401:
                        logger.warning("github_api_unauthorized")
                        if self._on_unauthorized and not unauthorized_retried:
                            new_tok = await self._on_unauthorized()
                            if new_tok:
                                self._token = new_tok
                                unauthorized_retried = True
                                continue
                        return resp

                    if resp.status_code == 403:
                        rl = resp.headers.get("X-RateLimit-Remaining", "")
                        if rl == "0":
                            logger.warning("github_rate_limit_exhausted_backoff")
                            await asyncio.sleep(delay)
                            delay = min(delay * 2, 120)
                            continue

                    if resp.status_code in (429, 503) and attempt < max_retries - 1:
                        ra = resp.headers.get("Retry-After")
                        wait = float(ra) if ra and ra.isdigit() else delay
                        logger.warning("github_status_retry", extra={"status": resp.status_code, "wait": wait})
                        await asyncio.sleep(wait)
                        delay = min(delay * 2, 120)
                        continue

                    if (
                        method == "GET"
                        and use_cache
                        and json_body is None
                        and resp.status_code == 200
                        and self._redis
                    ):
                        await self._set_cached(cache_key, resp.content)

                    return resp
                except (httpx.TimeoutException, httpx.NetworkError) as e:
                    last_exc = e
                    logger.warning("github_request_error attempt=%s", attempt + 1)
                    await asyncio.sleep(delay)
                    delay = min(delay * 2, 60)
            if last_exc:
                raise last_exc
            raise RuntimeError("GitHub request failed without response")

    async def get(self, path: str, *, params: dict[str, Any] | None = None) -> httpx.Response:
        return await self._request("GET", path, params=params)

    async def delete(self, path: str) -> httpx.Response:
        return await self._request("DELETE", path, use_cache=False)

    async def post_json(self, path: str, *, json_body: Any) -> dict[str, Any]:
        r = await self._request("POST", path, json_body=json_body, use_cache=False)
        if r.status_code >= 400:
            r.raise_for_status()
        return r.json()

    async def get_repository(self, owner: str, repo: str) -> dict[str, Any] | None:
        r = await self.get(f"/repos/{owner}/{repo}")
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.json()

    async def get_diff_for_pr(self, repo_full_name: str, pr_number: int) -> str | None:
        """Unified diff for a PR; None if PR/repo missing."""
        owner, repo = _split_repo(repo_full_name)
        r = await self._request(
            "GET",
            f"/repos/{owner}/{repo}/pulls/{pr_number}",
            headers_extra={"Accept": "application/vnd.github.diff"},
        )
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.text

    async def get_workflow_logs(self, repo_full_name: str, run_id: int) -> bytes | None:
        owner, repo = _split_repo(repo_full_name)
        r = await self._request(
            "GET",
            f"/repos/{owner}/{repo}/actions/runs/{run_id}/logs",
            use_cache=False,
            follow_redirects=True,
        )
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.content

    async def post_review_comment(
        self,
        repo_full_name: str,
        pr_number: int,
        body: str,
        *,
        commit_id: str | None = None,
        path: str | None = None,
        line: int | None = None,
    ) -> dict[str, Any] | None:
        """Inline review comment when commit_id+path+line; else issue review comment."""
        owner, repo = _split_repo(repo_full_name)
        payload: dict[str, Any] = {"body": body}
        if commit_id and path and line is not None:
            payload["commit_id"] = commit_id
            payload["path"] = path
            payload["line"] = line
            r = await self._request(
                "POST",
                f"/repos/{owner}/{repo}/pulls/{pr_number}/comments",
                json_body=payload,
                use_cache=False,
            )
        else:
            r = await self._request(
                "POST",
                f"/repos/{owner}/{repo}/pulls/{pr_number}/reviews",
                json_body={"body": body, "event": "COMMENT"},
                use_cache=False,
            )
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.json()

    async def list_files_in_repo(self, repo_full_name: str, *, ref: str | None = None) -> list[str]:
        """Recursive tree listing of file paths (blobs only)."""
        owner, repo = _split_repo(repo_full_name)
        repo_json = await self.get_repository(owner, repo)
        if not repo_json:
            return []
        branch = ref or repo_json.get("default_branch") or "main"
        ref_r = await self.get(f"/repos/{owner}/{repo}/git/ref/heads/{branch}")
        if ref_r.status_code == 404:
            return []
        ref_r.raise_for_status()
        sha = ref_r.json().get("object", {}).get("sha")
        if not sha:
            return []
        tree_r = await self.get(f"/repos/{owner}/{repo}/git/trees/{sha}", params={"recursive": "1"})
        if tree_r.status_code == 404:
            return []
        tree_r.raise_for_status()
        tree = tree_r.json()
        out: list[str] = []
        for item in tree.get("tree", []):
            if item.get("type") == "blob" and item.get("path"):
                out.append(str(item["path"]))
        return out

    async def get_file_content(self, repo_full_name: str, path: str, ref: str) -> str | None:
        owner, repo = _split_repo(repo_full_name)
        safe = quote(path.lstrip("/"), safe="/")
        r = await self.get(f"/repos/{owner}/{repo}/contents/{safe}", params={"ref": ref})
        if r.status_code == 404:
            return None
        r.raise_for_status()
        data = r.json()

        if isinstance(data, dict) and data.get("encoding") == "base64" and data.get("content"):
            return base64.b64decode(data["content"].replace("\n", "")).decode("utf-8", errors="replace")
        return None

    async def fetch_all_pull_requests_files(
        self,
        repo_full_name: str,
        *,
        state: str = "all",
    ) -> list[dict[str, Any]]:
        """Example paginated fetch (issues API style) — uses Link header."""
        owner, repo = _split_repo(repo_full_name)

        async def fetch_page(url: str) -> httpx.Response:
            return await self._request("GET", url, use_cache=False)

        first = f"{self._base}/repos/{owner}/{repo}/pulls?state={state}&per_page=100"
        return await fetch_all_pages_json(fetch_page, first, max_items=5000)

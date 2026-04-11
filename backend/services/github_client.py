"""Async GitHub REST API client with retries and basic rate-limit handling."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

from config import BaseAppSettings

logger = logging.getLogger(__name__)


class GitHubClient:
    """Thin async wrapper around GitHub REST API using httpx."""

    def __init__(self, settings: BaseAppSettings, token: str | None = None) -> None:
        self._token = token
        self._user_agent = f"Auditr-Backend/{settings.environment}"
        self._base = "https://api.github.com"

    def _headers(self, extra: dict[str, str] | None = None) -> dict[str, str]:
        h: dict[str, str] = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": self._user_agent,
        }
        if self._token:
            h["Authorization"] = f"Bearer {self._token}"
        if extra:
            h.update(extra)
        return h

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: Any = None,
        headers_extra: dict[str, str] | None = None,
        max_retries: int = 3,
        follow_redirects: bool = True,
    ) -> httpx.Response:
        url = path if path.startswith("http") else f"{self._base}{path}"
        delay = 1.0
        last_exc: Exception | None = None
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
                    if resp.status_code == 403:
                        rl = resp.headers.get("X-RateLimit-Remaining", "")
                        if rl == "0":
                            logger.warning("GitHub rate limit exhausted; backing off")
                            await asyncio.sleep(delay)
                            delay = min(delay * 2, 60)
                            continue
                    if resp.status_code in (429, 503) and attempt < max_retries - 1:
                        retry_after = resp.headers.get("Retry-After")
                        wait = float(retry_after) if retry_after else delay
                        logger.warning("GitHub %s; retrying in %ss", resp.status_code, wait)
                        await asyncio.sleep(wait)
                        delay = min(delay * 2, 60)
                        continue
                    return resp
                except (httpx.TimeoutException, httpx.NetworkError) as e:
                    last_exc = e
                    logger.warning("GitHub request error (attempt %s): %s", attempt + 1, e)
                    await asyncio.sleep(delay)
                    delay = min(delay * 2, 60)
            if last_exc:
                raise last_exc
            raise RuntimeError("GitHub request failed without response")

    async def get_repository(self, owner: str, repo: str) -> dict[str, Any]:
        r = await self._request("GET", f"/repos/{owner}/{repo}")
        r.raise_for_status()
        return r.json()

    async def fetch_pull_request_diff(self, owner: str, repo: str, pull_number: int) -> str:
        """Return unified diff text for a pull request."""
        r = await self._request(
            "GET",
            f"/repos/{owner}/{repo}/pulls/{pull_number}",
            headers_extra={"Accept": "application/vnd.github.diff"},
        )
        r.raise_for_status()
        return r.text

    async def fetch_workflow_logs(self, owner: str, repo: str, run_id: int) -> bytes:
        """
        Download workflow run logs (zip). GitHub redirects to a signed URL.
        """
        r = await self._request(
            "GET",
            f"/repos/{owner}/{repo}/actions/runs/{run_id}/logs",
            follow_redirects=True,
        )
        r.raise_for_status()
        return r.content

    async def post_review_comment(
        self,
        owner: str,
        repo: str,
        pull_number: int,
        body: str,
        *,
        commit_id: str | None = None,
        path: str | None = None,
        line: int | None = None,
    ) -> dict[str, Any]:
        """Post an inline review comment on a PR (optional file/line)."""
        payload: dict[str, Any] = {"body": body}
        if commit_id and path and line is not None:
            payload["commit_id"] = commit_id
            payload["path"] = path
            payload["line"] = line
            r = await self._request(
                "POST",
                f"/repos/{owner}/{repo}/pulls/{pull_number}/comments",
                json_body=payload,
            )
        else:
            r = await self._request(
                "POST",
                f"/repos/{owner}/{repo}/pulls/{pull_number}/reviews",
                json_body={
                    "body": body,
                    "event": "COMMENT",
                },
            )
        r.raise_for_status()
        return r.json()

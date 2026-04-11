"""GitHub OAuth 2.0 helpers (authorize URL, code exchange, scope constants)."""

from __future__ import annotations

import logging
from typing import Any
from urllib.parse import urlencode

import httpx

from config import BaseAppSettings

logger = logging.getLogger(__name__)

# https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/scopes-for-oauth-apps
GITHUB_OAUTH_SCOPES = ("repo", "admin:repo_hook", "read:org")


def github_authorize_url(*, settings: BaseAppSettings, state: str, redirect_uri: str | None = None) -> str:
    """Build GitHub authorize URL with required scopes."""
    if not settings.github_client_id:
        msg = "GITHUB_CLIENT_ID is not configured"
        raise ValueError(msg)
    rid = redirect_uri or settings.github_oauth_redirect_uri
    q = urlencode(
        {
            "client_id": settings.github_client_id,
            "redirect_uri": rid,
            "scope": " ".join(GITHUB_OAUTH_SCOPES),
            "state": state,
            "allow_signup": "true",
        },
    )
    return f"https://github.com/login/oauth/authorize?{q}"


async def exchange_code_for_token(
    *,
    code: str,
    redirect_uri: str,
    settings: BaseAppSettings,
) -> dict[str, Any]:
    """
    Exchange authorization code for an access token.
    Returns JSON from GitHub (access_token, token_type, scope, ...).
    Never log the response body.
    """
    if not settings.github_client_id or not settings.github_client_secret:
        msg = "GitHub OAuth is not configured"
        raise ValueError(msg)
    async with httpx.AsyncClient(timeout=30.0) as client:
        token_res = await client.post(
            "https://github.com/login/oauth/access_token",
            headers={"Accept": "application/json"},
            data={
                "client_id": settings.github_client_id,
                "client_secret": settings.github_client_secret,
                "code": code,
                "redirect_uri": redirect_uri,
            },
        )
        token_res.raise_for_status()
        data = token_res.json()
    if not data.get("access_token"):
        logger.warning("github_oauth_missing_access_token")
        raise ValueError("GitHub did not return an access token")
    return data


async def fetch_github_user(access_token: str) -> dict[str, Any]:
    """GET /user — never log token."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        user_res = await client.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        user_res.raise_for_status()
        return user_res.json()


def parse_scope_string(scope_header: str | None) -> str | None:
    if not scope_header:
        return None
    return scope_header.strip()

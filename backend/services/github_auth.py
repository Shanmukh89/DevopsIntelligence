"""GitHub OAuth 2.0 helpers (authorize URL, code exchange, scope constants)."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import urlencode

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import BaseAppSettings
from models.github_credentials import GitHubCredential
from models.user import User

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


async def refresh_oauth_access_token(*, refresh_token: str, settings: BaseAppSettings) -> dict[str, Any]:
    """
    Exchange refresh_token for new access token (when OAuth app has refresh tokens enabled).
    Response may include access_token, refresh_token, expires_in — never log body.
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
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            },
        )
        token_res.raise_for_status()
        data = token_res.json()
    if not data.get("access_token"):
        logger.warning("github_oauth_refresh_missing_access_token")
        raise ValueError("GitHub did not return an access token on refresh")
    return data


async def refresh_stored_github_access_token(
    *,
    db: AsyncSession,
    user: User,
    settings: BaseAppSettings,
    fernet_key: str,
) -> str | None:
    """
    If a refresh token is stored, exchange it and update encrypted credentials.
    Returns new plaintext access token, or None if refresh is not possible.
    """
    result = await db.execute(select(GitHubCredential).where(GitHubCredential.user_id == user.id))
    cred = result.scalar_one_or_none()
    if not cred or not cred.refresh_token_encrypted:
        return None
    try:
        old_refresh = GitHubCredential.decrypt_access_token(cred.refresh_token_encrypted, fernet_key=fernet_key)
    except Exception:
        logger.warning("github_refresh_decrypt_failed")
        return None
    try:
        data = await refresh_oauth_access_token(refresh_token=old_refresh, settings=settings)
    except (ValueError, httpx.HTTPError) as e:
        logger.warning("github_oauth_refresh_failed", extra={"err_type": type(e).__name__})
        return None
    cred.access_token_encrypted = GitHubCredential.encrypt_access_token(data["access_token"], fernet_key=fernet_key)
    if data.get("refresh_token"):
        cred.refresh_token_encrypted = GitHubCredential.encrypt_access_token(
            data["refresh_token"],
            fernet_key=fernet_key,
        )
    if data.get("scope"):
        cred.scopes = str(data["scope"]).strip()
    expires_in = data.get("expires_in")
    if expires_in is not None:
        try:
            cred.expires_at = datetime.now(tz=UTC) + timedelta(seconds=int(expires_in))
        except (TypeError, ValueError):
            cred.expires_at = None
    await db.flush()
    return data["access_token"]


def parse_scope_string(scope_header: str | None) -> str | None:
    if not scope_header:
        return None
    return scope_header.strip()

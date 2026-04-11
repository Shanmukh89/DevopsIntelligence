"""Authentication: GitHub OAuth, JWT verification, logout, request context."""

from __future__ import annotations

import logging
from contextvars import ContextVar
from typing import Annotated, Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from jose import JWTError, jwt
from pydantic import BaseModel, Field
from starlette.middleware.base import BaseHTTPMiddleware

from config import BaseAppSettings, get_settings
from deps import get_settings_dep

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])

# Request-scoped auth context (set by JWT middleware / dependencies)
auth_context: ContextVar[dict[str, Any] | None] = ContextVar("auth_context", default=None)


class GitHubCallbackBody(BaseModel):
    code: str = Field(..., min_length=1)
    redirect_uri: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


def create_access_token(
    subject: str,
    *,
    settings: BaseAppSettings,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    from datetime import UTC, datetime, timedelta

    expire = datetime.now(tz=UTC) + timedelta(minutes=settings.jwt_expire_minutes)
    payload: dict[str, Any] = {
        "sub": subject,
        "exp": int(expire.timestamp()),
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str, settings: BaseAppSettings) -> dict[str, Any]:
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])


async def _exchange_github_code(
    code: str,
    redirect_uri: str,
    settings: BaseAppSettings,
) -> tuple[str, dict[str, Any]]:
    if not settings.github_client_id or not settings.github_client_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GitHub OAuth is not configured",
        )
    async with httpx.AsyncClient(timeout=30.0) as client:
        token_res = await client.post(
            "https://github.com/login/oauth/access_token",
            headers={
                "Accept": "application/json",
            },
            data={
                "client_id": settings.github_client_id,
                "client_secret": settings.github_client_secret,
                "code": code,
                "redirect_uri": redirect_uri,
            },
        )
        token_res.raise_for_status()
        token_json = token_res.json()
        access_token = token_json.get("access_token")
        if not access_token:
            logger.warning("GitHub token response missing access_token: %s", token_json)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="GitHub did not return an access token",
            )
        user_res = await client.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github+json",
            },
        )
        user_res.raise_for_status()
        user = user_res.json()
        return access_token, user


@router.post("/github/callback", response_model=TokenResponse)
async def github_oauth_callback(
    body: GitHubCallbackBody,
    settings: Annotated[BaseAppSettings, Depends(get_settings_dep)],
) -> TokenResponse:
    """Exchange GitHub OAuth code and return our JWT for API access."""
    _, gh_user = await _exchange_github_code(body.code, body.redirect_uri, settings)
    sub = str(gh_user.get("id", ""))
    login = gh_user.get("login", "")
    jwt_token = create_access_token(
        sub,
        settings=settings,
        extra_claims={"login": login, "github": True},
    )
    logger.info("github_oauth_success login=%s", login)
    return TokenResponse(access_token=jwt_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout() -> None:
    """Client should discard JWT; server is stateless unless a denylist is added."""
    auth_context.set(None)
    logger.info("logout_requested")


def get_token_from_request(request: Request) -> str | None:
    auth = request.headers.get("authorization")
    if auth and auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return None


async def get_current_user(
    request: Request,
    settings: Annotated[BaseAppSettings, Depends(get_settings_dep)],
) -> dict[str, Any]:
    """Require a valid JWT (use as Depends)."""
    token = get_token_from_request(request)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        payload = decode_token(token, settings)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from None
    auth_context.set(payload)
    return payload


async def get_current_user_optional(
    request: Request,
    settings: Annotated[BaseAppSettings, Depends(get_settings_dep)],
) -> dict[str, Any] | None:
    """Optional JWT — returns None if missing or invalid."""
    token = get_token_from_request(request)
    if not token:
        return None
    try:
        payload = decode_token(token, settings)
    except JWTError:
        return None
    auth_context.set(payload)
    return payload


class JWTAuthMiddleware(BaseHTTPMiddleware):
    """Populate request.state.user and auth_context from Bearer JWT when present."""

    async def dispatch(self, request: Request, call_next):
        settings = get_settings()
        token = get_token_from_request(request)
        if token:
            try:
                payload = decode_token(token, settings)
                request.state.user = payload
                auth_context.set(payload)
            except JWTError:
                request.state.user = None
                auth_context.set(None)
        else:
            request.state.user = None
            auth_context.set(None)
        return await call_next(request)

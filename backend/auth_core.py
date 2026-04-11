"""JWT helpers, request auth dependency, and optional JWT middleware."""

from __future__ import annotations

from contextvars import ContextVar
from typing import Annotated, Any

from fastapi import Depends, HTTPException, Request, status
from jose import JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware

from config import BaseAppSettings, get_settings


def get_settings_dep() -> BaseAppSettings:
    return get_settings()

auth_context: ContextVar[dict[str, Any] | None] = ContextVar("auth_context", default=None)


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


def get_token_from_request(request: Request) -> str | None:
    auth = request.headers.get("authorization")
    if auth and auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return None


async def get_current_user(
    request: Request,
    settings: Annotated[BaseAppSettings, Depends(get_settings_dep)],
) -> dict[str, Any]:
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

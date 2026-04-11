"""FastAPI dependencies (services, DB, settings)."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from redis.asyncio import Redis
from redis.exceptions import RedisError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import BaseAppSettings, get_settings
from crypto import resolve_fernet_key
from database import get_db_session
from models import GitHubCredential, User
from auth_core import get_current_user
from services.github_client import GitHubClient

# Database session dependency (use `Depends(get_db)` in routes)
get_db = get_db_session


def get_settings_dep() -> BaseAppSettings:
    return get_settings()


def fernet_key_from_settings(settings: BaseAppSettings) -> str:
    return resolve_fernet_key(
        fernet_key=settings.fernet_key,
        environment=settings.environment,
        jwt_secret_key=settings.jwt_secret_key,
    )


_redis: Redis | None = None


async def get_redis(settings: Annotated[BaseAppSettings, Depends(get_settings_dep)]) -> Redis | None:
    """Shared async Redis client (optional)."""
    global _redis
    if _redis is None:
        try:
            _redis = Redis.from_url(settings.redis_url, decode_responses=False)
        except (RedisError, OSError, ValueError):
            return None
    return _redis


async def get_github_client(
    settings: Annotated[BaseAppSettings, Depends(get_settings_dep)],
    redis_client: Annotated[Redis | None, Depends(get_redis)],
) -> GitHubClient:
    return GitHubClient(settings, redis_client=redis_client)


async def get_github_client_for_user(
    request: Request,
    settings: Annotated[BaseAppSettings, Depends(get_settings_dep)],
    db: Annotated[AsyncSession, Depends(get_db)],
    redis_client: Annotated[Redis | None, Depends(get_redis)],
) -> GitHubClient:
    """GitHub API client using stored OAuth token for the authenticated user."""
    payload = await get_current_user(request, settings)
    sub = payload.get("sub")
    try:
        user_uuid = uuid.UUID(str(sub))
    except (ValueError, TypeError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or legacy token; sign in again",
        ) from e

    result = await db.execute(select(User).where(User.id == user_uuid))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    r = await db.execute(select(GitHubCredential).where(GitHubCredential.user_id == user.id))
    cred = r.scalar_one_or_none()
    if not cred:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GitHub is not connected; complete OAuth first",
        )

    key = fernet_key_from_settings(settings)
    token = cred.plaintext_token(fernet_key=key)
    return GitHubClient(settings, token=token, redis_client=redis_client)


async def get_current_db_user(
    request: Request,
    settings: Annotated[BaseAppSettings, Depends(get_settings_dep)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    payload = await get_current_user(request, settings)
    sub = payload.get("sub")
    try:
        user_uuid = uuid.UUID(str(sub))
    except (ValueError, TypeError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or legacy token",
        ) from e
    result = await db.execute(select(User).where(User.id == user_uuid))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user

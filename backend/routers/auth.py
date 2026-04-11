"""Authentication: GitHub OAuth, JWT, logout, /me."""

from __future__ import annotations

import logging
import secrets
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.responses import RedirectResponse
from jose import JWTError, jwt
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth_core import (
    create_access_token,
    decode_token,
    get_current_user,
    get_current_user_optional,
    get_settings_dep,
)
from config import BaseAppSettings
from deps import fernet_key_from_settings, get_db
from models.github_credentials import GitHubCredential
from models.teams import Team
from models.user import User
from services.github_auth import (
    exchange_code_for_token,
    fetch_github_user,
    github_authorize_url,
    parse_scope_string,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])


class GitHubCallbackBody(BaseModel):
    code: str = Field(..., min_length=1)
    redirect_uri: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MeResponse(BaseModel):
    user_id: str
    team_id: str
    github_login: str
    github_id: int


def _oauth_state_token(settings: BaseAppSettings) -> str:
    exp = datetime.now(tz=UTC) + timedelta(minutes=10)
    return jwt.encode(
        {
            "typ": "gh_oauth_state",
            "nonce": secrets.token_hex(16),
            "exp": int(exp.timestamp()),
        },
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def _verify_oauth_state(state: str, settings: BaseAppSettings) -> None:
    try:
        payload = jwt.decode(state, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid state") from e
    if payload.get("typ") != "gh_oauth_state":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid state")


@router.get("/github/login")
async def github_login(
    settings: Annotated[BaseAppSettings, Depends(get_settings_dep)],
    next: str | None = Query(None, alias="next"),
) -> RedirectResponse:
    """Redirect browser to GitHub OAuth authorize URL."""
    try:
        state = _oauth_state_token(settings)
        url = github_authorize_url(settings=settings, state=state)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e)) from e
    if next:
        # Store next in state is not done here — frontend should pass next in callback query if needed
        pass
    return RedirectResponse(url, status_code=status.HTTP_302_FOUND)


async def _complete_oauth(
    *,
    code: str,
    redirect_uri: str,
    settings: BaseAppSettings,
    db: AsyncSession,
) -> TokenResponse:
    try:
        token_json = await exchange_code_for_token(code=code, redirect_uri=redirect_uri, settings=settings)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        logger.exception("github_oauth_exchange_failed")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="OAuth exchange failed") from e

    access_token = token_json["access_token"]
    scopes = parse_scope_string(token_json.get("scope"))

    gh_user = await fetch_github_user(access_token)
    github_id = int(gh_user["id"])
    login = str(gh_user.get("login") or "")

    key = fernet_key_from_settings(settings)

    result = await db.execute(select(User).where(User.github_id == github_id))
    user = result.scalar_one_or_none()

    if user is None:
        team = Team(name=f"{login}'s workspace")
        db.add(team)
        await db.flush()
        user = User(github_id=github_id, login=login, team_id=team.id)
        db.add(user)
        await db.flush()
    else:
        user.login = login

    enc = GitHubCredential.encrypt_access_token(access_token, fernet_key=key)
    r2 = await db.execute(select(GitHubCredential).where(GitHubCredential.user_id == user.id))
    cred = r2.scalar_one_or_none()
    if cred:
        cred.access_token_encrypted = enc
        cred.team_id = user.team_id
        cred.scopes = scopes
    else:
        cred = GitHubCredential(
            team_id=user.team_id,
            user_id=user.id,
            access_token_encrypted=enc,
            installation_id=None,
            expires_at=None,
            scopes=scopes,
        )
        db.add(cred)

    await db.flush()
    jwt_token = create_access_token(
        str(user.id),
        settings=settings,
        extra_claims={
            "login": login,
            "github_id": github_id,
            "team_id": str(user.team_id),
            "github": True,
        },
    )
    logger.info("github_oauth_success login=%s", login)
    return TokenResponse(access_token=jwt_token)


@router.get("/github/callback", response_model=TokenResponse)
async def github_oauth_callback_get(
    settings: Annotated[BaseAppSettings, Depends(get_settings_dep)],
    db: Annotated[AsyncSession, Depends(get_db)],
    code: str = Query(...),
    state: str = Query(...),
) -> TokenResponse:
    _verify_oauth_state(state, settings)
    redirect_uri = settings.github_oauth_redirect_uri
    return await _complete_oauth(code=code, redirect_uri=redirect_uri, settings=settings, db=db)


@router.post("/github/callback", response_model=TokenResponse)
async def github_oauth_callback_post(
    body: GitHubCallbackBody,
    settings: Annotated[BaseAppSettings, Depends(get_settings_dep)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    """Legacy: exchange code without signed state (use GET callback in production)."""
    return await _complete_oauth(
        code=body.code,
        redirect_uri=body.redirect_uri,
        settings=settings,
        db=db,
    )


@router.post("/logout")
async def logout() -> Response:
    """Client should discard JWT; server is stateless unless a denylist is added."""
    logger.info("logout_requested")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=MeResponse)
async def me(
    request: Request,
    settings: Annotated[BaseAppSettings, Depends(get_settings_dep)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MeResponse:
    payload = await get_current_user(request, settings)
    sub = payload.get("sub")
    try:
        from uuid import UUID

        uid = UUID(str(sub))
    except (ValueError, TypeError) as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from e
    result = await db.execute(select(User).where(User.id == uid))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return MeResponse(
        user_id=str(user.id),
        team_id=str(user.team_id),
        github_login=user.login,
        github_id=user.github_id,
    )

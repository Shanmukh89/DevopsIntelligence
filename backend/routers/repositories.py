"""Connected GitHub repositories: connect, list, disconnect, webhook verify."""

from __future__ import annotations

import secrets
import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import BaseAppSettings
from deps import (
    get_current_db_user,
    get_db,
    get_github_client_for_user,
    get_settings_dep,
)
from models.repositories import Repository
from models.user import User
from services.github_client import GitHubClient
from services.github_webhook_setup import register_webhook, unregister_webhook, verify_webhook_active
from services.repo_indexing import index_repository

router = APIRouter(prefix="/api/repos", tags=["repositories"])


class ConnectRepoBody(BaseModel):
    full_name: str = Field(..., min_length=3, description='e.g. "owner/repo"')


class RepositoryOut(BaseModel):
    id: str
    full_name: str
    default_branch: str
    github_repo_id: int
    webhook_registered: bool
    created_at: datetime

    model_config = {"from_attributes": False}


class VerifyWebhookOut(BaseModel):
    ok: bool
    active: bool | None = None
    detail: str | None = None


def _split_full_name(full_name: str) -> tuple[str, str]:
    parts = full_name.strip().split("/", 1)
    if len(parts) != 2 or not parts[0] or not parts[1]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="full_name must be like owner/repo",
        )
    return parts[0], parts[1]


@router.post("", response_model=RepositoryOut)
async def connect_repository(
    body: ConnectRepoBody,
    user: Annotated[User, Depends(get_current_db_user)],
    settings: Annotated[BaseAppSettings, Depends(get_settings_dep)],
    db: Annotated[AsyncSession, Depends(get_db)],
    gh: Annotated[GitHubClient, Depends(get_github_client_for_user)],
) -> RepositoryOut:
    owner, repo = _split_full_name(body.full_name)
    data = await gh.get_repository(owner, repo)
    if not data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found or inaccessible")

    github_repo_id = int(data["id"])
    default_branch = str(data.get("default_branch") or "main")

    existing = await db.execute(
        select(Repository).where(
            Repository.team_id == user.team_id,
            Repository.github_repo_id == github_repo_id,
        ),
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Repository already connected")

    hook_secret = secrets.token_hex(32)
    base = settings.auditr_domain.rstrip("/")
    callback_url = f"{base}/webhooks/github"

    hook_id = await register_webhook(
        gh,
        owner,
        repo,
        callback_url=callback_url,
        secret=hook_secret,
    )

    row = Repository(
        team_id=user.team_id,
        github_repo_id=github_repo_id,
        full_name=str(data["full_name"]),
        default_branch=default_branch,
        webhook_secret=hook_secret,
        github_hook_id=hook_id,
        last_indexed_at=None,
    )
    db.add(row)
    await db.flush()

    index_repository.delay(str(row.id))

    return RepositoryOut(
        id=str(row.id),
        full_name=row.full_name,
        default_branch=row.default_branch,
        github_repo_id=row.github_repo_id,
        webhook_registered=True,
        created_at=row.created_at,
    )


@router.get("", response_model=list[RepositoryOut])
async def list_repositories(
    user: Annotated[User, Depends(get_current_db_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[RepositoryOut]:
    result = await db.execute(select(Repository).where(Repository.team_id == user.team_id))
    rows = result.scalars().all()
    return [
        RepositoryOut(
            id=str(r.id),
            full_name=r.full_name,
            default_branch=r.default_branch,
            github_repo_id=r.github_repo_id,
            webhook_registered=r.github_hook_id is not None,
            created_at=r.created_at,
        )
        for r in rows
    ]


@router.get("/{repo_id}", response_model=RepositoryOut)
async def get_repository(
    repo_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_db_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RepositoryOut:
    result = await db.execute(
        select(Repository).where(Repository.id == repo_id, Repository.team_id == user.team_id),
    )
    r = result.scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")
    return RepositoryOut(
        id=str(r.id),
        full_name=r.full_name,
        default_branch=r.default_branch,
        github_repo_id=r.github_repo_id,
        webhook_registered=r.github_hook_id is not None,
        created_at=r.created_at,
    )


@router.delete(
    "/{repo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def disconnect_repository(
    repo_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_db_user)],
    settings: Annotated[BaseAppSettings, Depends(get_settings_dep)],
    db: Annotated[AsyncSession, Depends(get_db)],
    gh: Annotated[GitHubClient, Depends(get_github_client_for_user)],
) -> None:
    result = await db.execute(
        select(Repository).where(Repository.id == repo_id, Repository.team_id == user.team_id),
    )
    r = result.scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")

    owner, name = _split_full_name(r.full_name)
    if r.github_hook_id:
        await unregister_webhook(gh, owner, name, int(r.github_hook_id))

    await db.delete(r)
    await db.flush()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{repo_id}/verify-webhook", response_model=VerifyWebhookOut)
async def verify_webhook(
    repo_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_db_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    gh: Annotated[GitHubClient, Depends(get_github_client_for_user)],
) -> VerifyWebhookOut:
    result = await db.execute(
        select(Repository).where(Repository.id == repo_id, Repository.team_id == user.team_id),
    )
    r = result.scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")
    if not r.github_hook_id:
        return VerifyWebhookOut(ok=False, active=False, detail="No webhook id stored")
    owner, name = _split_full_name(r.full_name)
    active = await verify_webhook_active(gh, owner, name, int(r.github_hook_id))
    return VerifyWebhookOut(ok=True, active=active, detail="success" if active else "inactive_or_missing")

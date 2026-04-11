"""Slack integration: OAuth, webhooks, channels, interactive actions."""

from __future__ import annotations

import json
import logging
import uuid
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any
from urllib.parse import parse_qs, quote

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse, RedirectResponse
from jose import jwt
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth_core import get_current_user, get_settings_dep
from config import BaseAppSettings
from crypto import decrypt_secret_string, encrypt_secret_string, resolve_fernet_key
from deps import get_db
from models.slack_integration import SlackIntegration
from models.teams import Team
from services.slack_async_client import AsyncSlackClient
from services.slack_message_handler import decode_slack_oauth_state, handle_interactive_payload
from services.slack_signing import verify_slack_signature

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/integrations", tags=["integrations"])


def _fernet_key(settings: BaseAppSettings) -> str:
    return resolve_fernet_key(
        fernet_key=settings.fernet_key,
        environment=settings.environment,
        jwt_secret_key=settings.jwt_secret_key,
    )


def _slack_oauth_state_token(team_id: uuid.UUID, redirect_uri: str, settings: BaseAppSettings) -> str:
    expire = datetime.now(tz=UTC) + timedelta(minutes=15)
    payload: dict[str, Any] = {
        "sub": str(team_id),
        "exp": int(expire.timestamp()),
        "slack_oauth": True,
        "redirect_uri": redirect_uri,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


class SlackConnectOAuthBody(BaseModel):
    team_id: uuid.UUID
    code: str = Field(..., min_length=1)
    redirect_uri: str = Field(..., min_length=1)


class SlackConnectWebhookBody(BaseModel):
    team_id: uuid.UUID
    webhook_url: str = Field(..., min_length=8)


class SlackDisconnectBody(BaseModel):
    team_id: uuid.UUID


async def _exchange_slack_oauth(
    *,
    code: str,
    redirect_uri: str,
    settings: BaseAppSettings,
) -> dict[str, Any]:
    if not settings.slack_client_id or not settings.slack_client_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Slack OAuth is not configured",
        )
    async with httpx.AsyncClient(timeout=40.0) as client:
        resp = await client.post(
            "https://slack.com/api/oauth.v2.access",
            data={
                "client_id": settings.slack_client_id,
                "client_secret": settings.slack_client_secret,
                "code": code,
                "redirect_uri": redirect_uri,
            },
        )
        resp.raise_for_status()
        data = resp.json()
    if not data.get("ok"):
        logger.warning("slack_oauth_exchange_failed error=%s", data.get("error"))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Slack OAuth exchange failed",
        )
    return data


async def _save_oauth_integration(
    session: AsyncSession,
    team_id: uuid.UUID,
    oauth_json: dict[str, Any],
    settings: BaseAppSettings,
) -> SlackIntegration:
    token = oauth_json.get("access_token")
    if not token:
        raise HTTPException(status_code=400, detail="Slack did not return access_token")
    team_info = oauth_json.get("team") or {}
    workspace_id = team_info.get("id")
    workspace_name = team_info.get("name")
    incoming = oauth_json.get("incoming_webhook") or {}
    default_ch = incoming.get("channel_id")

    enc = encrypt_secret_string(token, fernet_key=_fernet_key(settings))
    existing = await session.execute(select(SlackIntegration).where(SlackIntegration.team_id == team_id))
    row = existing.scalar_one_or_none()
    if row:
        row.integration_type = "oauth"
        row.bot_token_encrypted = enc
        row.webhook_url_encrypted = None
        row.workspace_id = workspace_id
        row.workspace_name = workspace_name
        if default_ch:
            row.default_channel = default_ch
        return row

    row = SlackIntegration(
        team_id=team_id,
        workspace_id=workspace_id,
        workspace_name=workspace_name,
        integration_type="oauth",
        bot_token_encrypted=enc,
        default_channel=default_ch,
        channels_config={},
    )
    session.add(row)
    return row


@router.get("/slack/status")
async def slack_status(
    team_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[dict[str, Any], Depends(get_current_user)],
) -> dict[str, Any]:
    r = await db.execute(select(SlackIntegration).where(SlackIntegration.team_id == team_id))
    row = r.scalar_one_or_none()
    if not row:
        return {"connected": False}
    return {
        "connected": True,
        "integration_type": row.integration_type,
        "workspace_id": row.workspace_id,
        "workspace_name": row.workspace_name,
        "default_channel": row.default_channel,
    }


@router.post("/slack/connect")
async def slack_connect(
    body: dict[str, Any],
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[BaseAppSettings, Depends(get_settings_dep)],
    _user: Annotated[dict[str, Any], Depends(get_current_user)],
) -> dict[str, str]:
    """Connect via OAuth (code + redirect_uri) or incoming webhook URL."""
    mode = body.get("mode", "oauth")
    team_id = uuid.UUID(str(body["team_id"]))

    team = await db.get(Team, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    if mode == "webhook":
        wh = SlackConnectWebhookBody.model_validate(body)
        enc = encrypt_secret_string(wh.webhook_url, fernet_key=_fernet_key(settings))
        r = await db.execute(select(SlackIntegration).where(SlackIntegration.team_id == wh.team_id))
        row = r.scalar_one_or_none()
        if row:
            row.integration_type = "webhook"
            row.webhook_url_encrypted = enc
            row.bot_token_encrypted = None
        else:
            db.add(
                SlackIntegration(
                    team_id=wh.team_id,
                    integration_type="webhook",
                    webhook_url_encrypted=enc,
                    channels_config={},
                )
            )
        return {"status": "connected"}

    oauth = SlackConnectOAuthBody.model_validate(body)
    oauth_json = await _exchange_slack_oauth(
        code=oauth.code,
        redirect_uri=oauth.redirect_uri,
        settings=settings,
    )
    await _save_oauth_integration(db, oauth.team_id, oauth_json, settings)
    return {"status": "connected"}


@router.post(
    "/slack/disconnect",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def slack_disconnect(
    body: SlackDisconnectBody,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[dict[str, Any], Depends(get_current_user)],
) -> None:
    r = await db.execute(select(SlackIntegration).where(SlackIntegration.team_id == body.team_id))
    row = r.scalar_one_or_none()
    if row:
        await db.delete(row)
    return None


@router.get("/slack/channels")
async def slack_channels(
    team_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[BaseAppSettings, Depends(get_settings_dep)],
    _user: Annotated[dict[str, Any], Depends(get_current_user)],
) -> dict[str, Any]:
    r = await db.execute(select(SlackIntegration).where(SlackIntegration.team_id == team_id))
    integration = r.scalar_one_or_none()
    if not integration or integration.integration_type != "oauth" or not integration.bot_token_encrypted:
        raise HTTPException(status_code=400, detail="Slack bot not connected")

    token = decrypt_secret_string(integration.bot_token_encrypted, fernet_key=_fernet_key(settings))
    slack = AsyncSlackClient()
    out = await slack.conversations_list(
        token,
        types="public_channel,private_channel",
        exclude_archived="true",
        limit="200",
    )
    if not out.get("ok"):
        raise HTTPException(status_code=502, detail=out.get("error", "slack_api_error"))
    channels = []
    for ch in out.get("channels") or []:
        channels.append(
            {
                "id": ch.get("id"),
                "name": ch.get("name"),
                "is_private": ch.get("is_private", False),
            }
        )
    return {"channels": channels}


@router.get("/slack/oauth/authorize")
async def slack_oauth_authorize(
    settings: Annotated[BaseAppSettings, Depends(get_settings_dep)],
    _user: Annotated[dict[str, Any], Depends(get_current_user)],
    team_id: uuid.UUID = Query(...),
    redirect_uri: str = Query(..., min_length=1),
) -> dict[str, str]:
    if not settings.slack_client_id:
        raise HTTPException(status_code=503, detail="Slack OAuth is not configured")
    state = _slack_oauth_state_token(team_id, redirect_uri, settings)
    scope = quote("chat:write,files:write,channels:read")
    url = (
        f"https://slack.com/oauth/v2/authorize"
        f"?client_id={quote(settings.slack_client_id)}"
        f"&scope={scope}"
        f"&redirect_uri={quote(redirect_uri)}"
        f"&state={quote(state)}"
    )
    return {"authorization_url": url}


@router.get("/slack/oauth/callback")
async def slack_oauth_callback(
    code: str,
    state: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[BaseAppSettings, Depends(get_settings_dep)],
) -> RedirectResponse:
    """Browser redirect target for Slack OAuth (saves integration, then sends user to dashboard)."""
    try:
        team_id, redirect_uri = decode_slack_oauth_state(state, settings)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid state") from None
    oauth_json = await _exchange_slack_oauth(code=code, redirect_uri=redirect_uri, settings=settings)
    await _save_oauth_integration(db, team_id, oauth_json, settings)
    return RedirectResponse(
        url=f"{settings.auditr_dashboard_base_url.rstrip('/')}/integrations?slack=connected",
        status_code=status.HTTP_302_FOUND,
    )


@router.post("/slack/interactive")
async def slack_interactive(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[BaseAppSettings, Depends(get_settings_dep)],
) -> JSONResponse:
    raw = await request.body()
    ts = request.headers.get("X-Slack-Request-Timestamp")
    sig = request.headers.get("X-Slack-Signature")
    if not verify_slack_signature(
        signing_secret=settings.slack_signing_secret,
        body=raw,
        timestamp_header=ts,
        signature_header=sig,
    ):
        raise HTTPException(status_code=403, detail="Invalid signature")

    form = parse_qs(raw.decode("utf-8"))
    payload_raw = (form.get("payload") or [None])[0]
    if not payload_raw:
        raise HTTPException(status_code=400, detail="Missing payload")
    try:
        payload = json.loads(payload_raw)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail="Invalid payload") from e

    logger.info("slack_interactive %s", json.dumps({"type": payload.get("type"), "team": (payload.get("team") or {}).get("id")}))
    result = await handle_interactive_payload(session=db, settings=settings, payload=payload)
    return JSONResponse(content=result)


@router.get("/slack/track")
async def slack_track_github(
    u: str = Query(..., min_length=1, description="Destination URL (GitHub)"),
) -> RedirectResponse:
    """Log analytics then redirect to GitHub (or other target)."""
    logger.info(
        "slack_link_track",
        extra={"action_taken": "github_click", "destination_host": u.split("/")[2] if "://" in u else ""},
    )
    return RedirectResponse(url=u, status_code=status.HTTP_302_FOUND)


@router.get("/health/slack")
async def slack_integration_health(
    settings: Annotated[BaseAppSettings, Depends(get_settings_dep)],
) -> dict[str, bool]:
    """Non-secret readiness: OAuth client id and signing secret configured."""
    return {
        "oauth_configured": bool(settings.slack_client_id and settings.slack_client_secret),
        "signing_secret_configured": bool(settings.slack_signing_secret),
    }

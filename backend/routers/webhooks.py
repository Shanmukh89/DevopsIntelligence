"""GitHub webhooks: signature verification, persistence, Celery dispatch."""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import logging
from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import select

from config import BaseAppSettings
from deps import get_db, get_settings_dep
from models.repositories import Repository
from models.webhook_event import WebhookEvent
from services.webhook_processor import enqueue_github_event, preview_dispatch_note

logger = logging.getLogger(__name__)

router = APIRouter(tags=["webhooks"])


def _verify_github_signature(secret: str, payload: bytes, signature_header: str | None) -> bool:
    if not signature_header or not signature_header.startswith("sha256="):
        return False
    expected = signature_header.partition("=")[2]
    mac = hmac.new(secret.encode("utf-8"), msg=payload, digestmod=hashlib.sha256)
    digest = mac.hexdigest()
    return hmac.compare_digest(digest, expected)


def _payload_summary(payload: dict[str, Any], max_len: int = 512) -> str:
    try:
        s = json.dumps(payload, default=str)[:max_len]
    except (TypeError, ValueError):
        s = str(payload)[:max_len]
    return s


@router.post("/webhooks/github")
async def github_webhook(
    request: Request,
    settings: Annotated[BaseAppSettings, Depends(get_settings_dep)],
    db: Annotated[AsyncSession, Depends(get_db)],
    x_github_event: Annotated[str | None, Header(alias="X-GitHub-Event")] = None,
    x_github_delivery: Annotated[str | None, Header(alias="X-GitHub-Delivery")] = None,
    x_hub_signature_256: Annotated[str | None, Header(alias="X-Hub-Signature-256")] = None,
) -> Response:
    """Accept GitHub webhooks: verify HMAC, log to DB, queue Celery, return 200 quickly."""
    raw_body = await request.body()
    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON") from e

    repo_fn = (payload.get("repository") or {}).get("full_name")
    verified = False
    if repo_fn:
        r = await db.execute(select(Repository).where(Repository.full_name == repo_fn))
        row = r.scalar_one_or_none()
        if row and row.webhook_secret:
            verified = _verify_github_signature(row.webhook_secret, raw_body, x_hub_signature_256)
    if not verified:
        verified = _verify_github_signature(settings.github_webhook_secret, raw_body, x_hub_signature_256)
    if not verified:
        logger.warning("invalid_github_webhook_signature delivery=%s", x_github_delivery)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid signature")

    event_type = x_github_event or "unknown"
    action = payload.get("action")
    repo = repo_fn

    dispatch_note = preview_dispatch_note(event_type, payload)
    if dispatch_note is None:
        dispatch_note = f"no_handler:{event_type}:{action}"
    else:

        async def _enqueue() -> None:
            try:
                await asyncio.to_thread(enqueue_github_event, event_type, payload)
            except Exception:
                logger.exception(
                    "webhook_enqueue_failed",
                    extra={"event_type": event_type, "action_taken": "celery_enqueue_error"},
                )

        asyncio.create_task(_enqueue())

    received_at = datetime.now(tz=UTC)
    row = WebhookEvent(
        event_type=event_type,
        delivery_id=x_github_delivery,
        action=action,
        repository_full_name=repo,
        payload_summary=_payload_summary(payload),
        payload_json=payload,
        processing_note=dispatch_note,
        received_at=received_at,
    )
    db.add(row)
    await db.flush()

    logger.info(
        "webhook_received",
        extra={
            "event_type": event_type,
            "action": action,
            "delivery": x_github_delivery,
            "repository": repo,
            "dispatch": dispatch_note,
        },
    )

    return Response(status_code=status.HTTP_200_OK)

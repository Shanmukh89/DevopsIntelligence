"""Slack formatting, API routes, and interactive handler (mocked HTTP)."""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from urllib.parse import urlencode

import pytest
from fastapi.testclient import TestClient

from config import clear_settings_cache, get_settings
from services.slack_templates import build_failure_message


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("ENVIRONMENT", "test")
    clear_settings_cache()
    from main import create_app

    return TestClient(create_app())


def test_slack_status_requires_auth(client: TestClient) -> None:
    r = client.get(
        "/api/integrations/slack/status",
        params={"team_id": "00000000-0000-0000-0000-000000000002"},
    )
    assert r.status_code == 401


def test_slack_health(client: TestClient) -> None:
    r = client.get("/api/integrations/health/slack")
    assert r.status_code == 200
    body = r.json()
    assert "oauth_configured" in body
    assert "signing_secret_configured" in body


def test_build_failure_message_structure() -> None:
    msg = build_failure_message(
        repo_full_name="org/auditr",
        build_label="Run `1` • `main` • `abc1234`",
        explanation="Compiler error in module X.",
        so_results=[{"title": "How to fix X", "link": "https://stackoverflow.com/q/1"}],
        github_url="https://github.com/org/auditr/actions/runs/1",
        auditr_url="http://localhost:3000/repos/r/builds/b",
        dismiss_value="dismiss|build|00000000-0000-0000-0000-000000000003|00000000-0000-0000-0000-000000000004",
        use_tracked_github_button=True,
        track_base_url="http://localhost:8000",
    )
    assert "attachments" in msg
    att = msg["attachments"][0]
    assert att.get("color")
    blocks = att.get("blocks") or []
    texts = json.dumps(blocks)
    assert "Build failed" in texts
    assert "Stack Overflow" in texts
    assert "Dismiss Alert" in texts


def _sign_slack_request(body: bytes, signing_secret: str, ts: str | None = None) -> dict[str, str]:
    if ts is None:
        ts = str(int(time.time()))
    sig_basestring = f"v0:{ts}:{body.decode('utf-8')}"
    sig = (
        "v0="
        + hmac.new(signing_secret.encode("utf-8"), sig_basestring.encode("utf-8"), hashlib.sha256).hexdigest()
    )
    return {"X-Slack-Request-Timestamp": ts, "X-Slack-Signature": sig}


def test_slack_interactive_invalid_signature(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("SLACK_SIGNING_SECRET", "test_signing_secret")
    clear_settings_cache()

    payload = {
        "type": "block_actions",
        "team": {"id": "T123"},
        "actions": [{"action_id": "dismiss_alert", "value": "dismiss|vuln|x|y"}],
    }
    body = urlencode({"payload": json.dumps(payload)}).encode("utf-8")
    r = client.post(
        "/api/integrations/slack/interactive",
        content=body,
        headers={"Content-Type": "application/x-www-form-urlencoded", "X-Slack-Signature": "v0=bad"},
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_handle_dismiss_creates_row(monkeypatch: pytest.MonkeyPatch) -> None:
    import uuid

    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from sqlalchemy.pool import StaticPool

    from database import Base
    from models.slack_integration import SlackAlertDismissal, SlackIntegration
    from models.teams import Team
    from services.slack_message_handler import handle_interactive_payload

    monkeypatch.setenv("ENVIRONMENT", "test")
    clear_settings_cache()
    settings = get_settings()

    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(engine, expire_on_commit=False)
    team_id = uuid.uuid4()
    async with async_session() as session:
        session.add(Team(id=team_id, name="t"))
        session.add(
            SlackIntegration(
                team_id=team_id,
                workspace_id="T123",
                integration_type="oauth",
                bot_token_encrypted=None,
                channels_config={},
            )
        )
        await session.commit()

    async with async_session() as session:
        payload = {
            "type": "block_actions",
            "team": {"id": "T123"},
            "actions": [
                {
                    "action_id": "dismiss_alert",
                    "value": f"dismiss|cost|{team_id}|summary",
                }
            ],
        }
        out = await handle_interactive_payload(session=session, settings=settings, payload=payload)
        await session.commit()
        assert "Auditr" in out.get("text", "")

    async with async_session() as session:
        r = await session.execute(select(SlackAlertDismissal).where(SlackAlertDismissal.team_id == team_id))
        assert r.scalar_one_or_none() is not None

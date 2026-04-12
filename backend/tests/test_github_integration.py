"""GitHub OAuth, webhooks, and rate limiting (mocked HTTP)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient

from auth_core import decode_token
from config import clear_settings_cache, get_settings
from main import create_app


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("GITHUB_CLIENT_ID", "test-client-id")
    monkeypatch.setenv("GITHUB_CLIENT_SECRET", "test-secret")
    clear_settings_cache()
    app = create_app()
    with TestClient(app) as c:
        yield c


def test_github_login_redirect(client: TestClient) -> None:
    r = client.get("/api/auth/github/login", follow_redirects=False)
    assert r.status_code == 302
    loc = r.headers.get("location", "")
    assert "github.com/login/oauth/authorize" in loc
    assert "scope=" in loc.replace("+", " ")
    assert "repo" in loc
    assert "admin%3Arepo_hook" in loc or "admin:repo_hook" in loc.replace("%3A", ":")
    assert "read%3Aorg" in loc or "read:org" in loc.replace("%3A", ":")


def test_oauth_callback_stores_encrypted_token(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "test")
    clear_settings_cache()
    settings = get_settings()
    from jose import jwt

    state = jwt.encode(
        {"typ": "gh_oauth_state", "nonce": "abc", "exp": 9999999999},
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    async def fake_exchange(**kwargs: object) -> dict:
        return {"access_token": "ghs_test_token", "scope": "repo"}

    async def fake_user(token: str) -> dict:
        return {"id": 424242, "login": "testuser"}

    with (
        patch("routers.auth.exchange_code_for_token", fake_exchange),
        patch("routers.auth.fetch_github_user", fake_user),
    ):
        r = client.get(
            "/api/auth/github/callback",
            params={"code": "abc", "state": state},
        )
    assert r.status_code == 200
    body = r.json()
    assert "access_token" in body
    token = body["access_token"]
    payload = decode_token(token, settings)
    assert payload.get("login") == "testuser"


def test_me_requires_jwt(client: TestClient) -> None:
    r = client.get("/api/auth/me")
    assert r.status_code == 401


def test_list_repos_empty_after_oauth(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "test")
    clear_settings_cache()
    settings = get_settings()
    from jose import jwt

    state = jwt.encode(
        {"typ": "gh_oauth_state", "nonce": "x", "exp": 9999999999},
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    async def fake_exchange(**kwargs: object) -> dict:
        return {"access_token": "tok", "scope": "repo"}

    async def fake_user(token: str) -> dict:
        return {"id": 999001, "login": "solo"}

    with (
        patch("routers.auth.exchange_code_for_token", fake_exchange),
        patch("routers.auth.fetch_github_user", fake_user),
    ):
        r = client.get("/api/auth/github/callback", params={"code": "c", "state": state})
    assert r.status_code == 200
    jwt_token = r.json()["access_token"]

    lr = client.get("/api/repos", headers={"Authorization": f"Bearer {jwt_token}"})
    assert lr.status_code == 200
    assert lr.json() == []


def test_rate_limit_headers_update(monkeypatch: pytest.MonkeyPatch) -> None:
    from services import github_rate_limiter

    github_rate_limiter._snapshot.limit = None
    resp = httpx.Response(
        200,
        headers={
            "X-RateLimit-Limit": "5000",
            "X-RateLimit-Remaining": "5",
            "X-RateLimit-Reset": "1700000000",
            "X-RateLimit-Resource": "core",
        },
    )
    github_rate_limiter.update_from_response(resp)
    snap = github_rate_limiter.snapshot()
    assert snap.limit == 5000
    assert snap.remaining == 5


def test_webhook_registration_payload() -> None:
    from services.github_webhook_setup import register_webhook

    calls: list[dict] = []

    async def capture_post_json(path: str, *, json_body: dict) -> dict:
        calls.append({"path": path, "body": json_body})
        return {"id": 12345, "active": True}

    gh = MagicMock()
    gh.post_json = AsyncMock(side_effect=capture_post_json)

    import asyncio

    asyncio.run(
        register_webhook(
            gh,
            "o",
            "r",
            callback_url="https://example.com/webhooks/github",
            secret="sekrit",
        ),
    )
    assert calls[0]["path"] == "/repos/o/r/hooks"
    assert calls[0]["body"]["events"] == ["pull_request", "workflow_run", "push"]
    assert calls[0]["body"]["config"]["url"] == "https://example.com/webhooks/github"


def test_pagination_parse_next() -> None:
    from services.github_pagination import parse_next_url

    link = '<https://api.github.com/repos/o/r/issues?page=2>; rel="next", <...>; rel="last"'
    assert "page=2" in (parse_next_url(link) or "")


@pytest.mark.asyncio
async def test_github_client_retries_once_on_401_after_refresh() -> None:
    from config import get_settings
    from services.github_client import GitHubClient

    settings = get_settings()
    calls = {"n": 0}

    async def refresh() -> str | None:
        return "new-token"

    async def fake_request(self: object, method: str, url: str, **kwargs: object) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(401, request=httpx.Request(method, url))
        return httpx.Response(200, json={"ok": True}, request=httpx.Request(method, url))

    gh = GitHubClient(settings, token="old", on_unauthorized=refresh)
    import services.github_client as gc

    with patch.object(gc.httpx.AsyncClient, "request", new=fake_request):
        r = await gh.get("/user")
    assert r.status_code == 200


def test_schedule_rate_limited_retry_uses_celery_delay(monkeypatch: pytest.MonkeyPatch) -> None:
    from services import github_rate_limiter

    sent: list[tuple] = []

    def fake_delay(*args: object, **kwargs: object) -> None:
        sent.append((args, kwargs))

    monkeypatch.setattr(github_rate_limiter.retry_http_task, "delay", fake_delay)
    github_rate_limiter.schedule_rate_limited_retry("repos.index_repository", args=["id"], kwargs={})
    assert sent
    args, _kw = sent[0]
    assert args[0] == "repos.index_repository"


def test_verify_webhook_endpoint(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "test")
    clear_settings_cache()
    settings = get_settings()
    from jose import jwt

    state = jwt.encode(
        {"typ": "gh_oauth_state", "nonce": "vw", "exp": 9999999999},
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    async def fake_exchange(**kwargs: object) -> dict:
        return {"access_token": "tok", "scope": "repo"}

    async def fake_user(token: str) -> dict:
        return {"id": 888002, "login": "whuser"}

    with (
        patch("routers.auth.exchange_code_for_token", fake_exchange),
        patch("routers.auth.fetch_github_user", fake_user),
    ):
        r = client.get("/api/auth/github/callback", params={"code": "c", "state": state})
    assert r.status_code == 200
    jwt_token = r.json()["access_token"]

    with patch(
        "routers.repositories.verify_webhook_active",
        new=AsyncMock(return_value=True),
    ):
        from uuid import uuid4

        fake_id = str(uuid4())
        vr = client.post(
            f"/api/repos/{fake_id}/verify-webhook",
            headers={"Authorization": f"Bearer {jwt_token}"},
        )
    assert vr.status_code == 404

    with (
        patch("routers.repositories.register_webhook", AsyncMock(return_value=99)),
        patch(
            "services.repo_indexing.index_repository.delay",
            MagicMock(),
        ),
    ):
        from services.github_client import GitHubClient

        async def fake_repo(owner: str, repo: str) -> dict:
            return {
                "id": 4242,
                "full_name": f"{owner}/{repo}",
                "default_branch": "main",
            }

        gh_mock = MagicMock(spec=GitHubClient)
        gh_mock.get_repository = AsyncMock(side_effect=fake_repo)

        async def override_gh():
            return gh_mock

        app = client.app
        from deps import get_github_client_for_user

        app.dependency_overrides[get_github_client_for_user] = override_gh
        try:
            pr = client.post(
                "/api/repos",
                json={"full_name": "demo/hello"},
                headers={"Authorization": f"Bearer {jwt_token}"},
            )
        finally:
            app.dependency_overrides.pop(get_github_client_for_user, None)

    assert pr.status_code == 200
    repo_id = pr.json()["id"]

    with patch(
        "routers.repositories.verify_webhook_active",
        new=AsyncMock(return_value=True),
    ):
        vr2 = client.post(
            f"/api/repos/{repo_id}/verify-webhook",
            headers={"Authorization": f"Bearer {jwt_token}"},
        )
    assert vr2.status_code == 200
    body = vr2.json()
    assert body["ok"] is True
    assert body["active"] is True
    assert body["detail"] == "success"

"""Register and manage GitHub repository webhooks."""

from __future__ import annotations

import logging
from typing import Any

from services.github_client import GitHubClient

logger = logging.getLogger(__name__)

DEFAULT_EVENTS = ("pull_request", "workflow_run", "push")


async def register_webhook(
    client: GitHubClient,
    owner: str,
    repo: str,
    *,
    callback_url: str,
    secret: str,
    events: tuple[str, ...] = DEFAULT_EVENTS,
) -> int:
    """POST /repos/{owner}/{repo}/hooks — returns GitHub hook id."""
    payload: dict[str, Any] = {
        "name": "web",
        "active": True,
        "events": list(events),
        "config": {
            "url": callback_url,
            "content_type": "json",
            "secret": secret,
            "insecure_ssl": "0",
        },
    }
    data = await client.post_json(f"/repos/{owner}/{repo}/hooks", json_body=payload)
    hook_id = data.get("id")
    if not isinstance(hook_id, int):
        logger.warning("github_hook_missing_id")
        raise RuntimeError("GitHub did not return hook id")
    return hook_id


async def verify_webhook_active(
    client: GitHubClient,
    owner: str,
    repo: str,
    hook_id: int,
) -> bool:
    """GET hook; ensure active."""
    r = await client.get(f"/repos/{owner}/{repo}/hooks/{hook_id}")
    if r.status_code == 404:
        return False
    r.raise_for_status()
    body = r.json()
    return bool(body.get("active", False))


async def unregister_webhook(
    client: GitHubClient,
    owner: str,
    repo: str,
    hook_id: int,
) -> bool:
    """DELETE hook. Returns False if already gone."""
    r = await client.delete(f"/repos/{owner}/{repo}/hooks/{hook_id}")
    if r.status_code == 404:
        return False
    r.raise_for_status()
    return True

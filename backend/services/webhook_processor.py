"""
GitHub webhook event handlers — executed in Celery workers only.

Public `process_*` coroutines schedule tasks and return immediately (for use from FastAPI).
"""

from __future__ import annotations

import logging
from typing import Any

from celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="webhooks.process_pull_request_opened", bind=True)
def process_pull_request_opened_task(self, payload: dict[str, Any]) -> str:
    """Handle pull_request with action opened (sync Celery task)."""
    repo = (payload.get("repository") or {}).get("full_name", "?")
    pr = payload.get("pull_request") or {}
    num = pr.get("number")
    logger.info(
        "celery_pr_opened",
        extra={
            "task_id": self.request.id,
            "repository": repo,
            "pull_number": num,
            "action_taken": "queued_processing",
        },
    )
    # Heavy work (diff fetch, AI, comments) belongs here — not inline on webhook.
    return f"pull_request_opened:{repo}#{num}"


@celery_app.task(name="webhooks.process_workflow_run_completed", bind=True)
def process_workflow_run_completed_task(self, payload: dict[str, Any]) -> str:
    """Handle workflow_run with action completed."""
    repo = (payload.get("repository") or {}).get("full_name", "?")
    wr = payload.get("workflow_run") or {}
    run_id = wr.get("id")
    logger.info(
        "celery_workflow_completed",
        extra={
            "task_id": self.request.id,
            "repository": repo,
            "run_id": run_id,
            "action_taken": "queued_log_processing",
        },
    )
    return f"workflow_run_completed:{repo}:{run_id}"


@celery_app.task(name="webhooks.process_push", bind=True)
def process_push_task(self, payload: dict[str, Any]) -> str:
    """Handle push events."""
    repo = (payload.get("repository") or {}).get("full_name", "?")
    ref = payload.get("ref")
    logger.info(
        "celery_push",
        extra={
            "task_id": self.request.id,
            "repository": repo,
            "ref": ref,
            "action_taken": "queued_push_processing",
        },
    )
    return f"push:{repo}:{ref}"


async def process_pull_request_opened(payload: dict[str, Any]) -> None:
    """Queue PR opened processing (non-blocking)."""
    process_pull_request_opened_task.delay(payload)
    logger.info("scheduled_pull_request_opened_task")


async def process_workflow_run_completed(payload: dict[str, Any]) -> None:
    """Queue workflow run completed processing."""
    process_workflow_run_completed_task.delay(payload)
    logger.info("scheduled_workflow_run_completed_task")


async def process_push(payload: dict[str, Any]) -> None:
    """Queue push event processing."""
    process_push_task.delay(payload)
    logger.info("scheduled_push_task")


def dispatch_github_event(event_type: str, payload: dict[str, Any]) -> str | None:
    """
    Route GitHub event to the appropriate Celery task.
    Returns a short note for logging / DB (task name or skip reason).
    """
    action = payload.get("action")
    if event_type == "pull_request" and action == "opened":
        process_pull_request_opened_task.delay(payload)
        return "queued:pull_request_opened"
    if event_type == "workflow_run" and action == "completed":
        process_workflow_run_completed_task.delay(payload)
        return "queued:workflow_run_completed"
    if event_type == "push":
        process_push_task.delay(payload)
        return "queued:push"
    return None

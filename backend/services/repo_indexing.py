"""Background repository indexing (Celery)."""

from __future__ import annotations

import logging

from celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="repos.index_repository")
def index_repository(repo_id: str) -> str:
    """Placeholder: clone / chunk / embed pipeline hooks in here."""
    logger.info("index_repository_scheduled", extra={"repo_id": repo_id, "action_taken": "celery_queued"})
    return repo_id

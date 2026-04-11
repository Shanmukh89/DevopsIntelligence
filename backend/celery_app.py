"""Celery application instance."""

from celery import Celery

from config import get_settings

_settings = get_settings()

celery_app = Celery(
    "auditr",
    broker=_settings.redis_url,
    backend=_settings.redis_url,
    include=["services.webhook_processor"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
)

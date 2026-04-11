"""Celery application instance."""

from celery import Celery

from config import get_settings

_settings = get_settings()

celery_app = Celery(
    "auditr",
    broker=_settings.redis_url,
    backend=_settings.redis_url,
    include=[
        "services.webhook_processor",
        "services.repo_indexing",
        "services.github_rate_limiter",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    broker_transport_options={
        "socket_connect_timeout": 5,
        "socket_timeout": 5,
        "retry_on_timeout": True,
    },
)

if getattr(_settings, "celery_task_always_eager", False):
    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True

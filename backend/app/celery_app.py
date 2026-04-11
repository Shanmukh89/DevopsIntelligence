import os

from celery import Celery

_redis = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "auditr",
    broker=_redis,
    backend=_redis,
    include=["app.tasks"],
)

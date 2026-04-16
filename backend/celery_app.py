"""
Auditr — Celery Application
Background task queue for scheduled and async jobs.
"""

from celery import Celery
from app.core.config import settings

# Use the URL from settings, and append /1 for the results backend
base_redis_url = settings.REDIS_URL.rsplit('/', 1)[0] if '/' in settings.REDIS_URL[9:] else settings.REDIS_URL

celery_app = Celery(
    "auditr",
    broker=settings.REDIS_URL,
    backend=f"{base_redis_url}/1",
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        # Daily vulnerability scan
        "vulnerability-scan": {
            "task": "celery_app.run_vulnerability_scan",
            "schedule": 86400.0,  # 24 hours
        },
        # Daily cloud cost analysis
        "cloud-cost-analysis": {
            "task": "celery_app.run_cloud_cost_analysis",
            "schedule": 86400.0,
        },
    },
)


# ---- Registered Celery Tasks ----
# These must be decorated functions so Celery's beat scheduler can discover them.

@celery_app.task(name="celery_app.run_vulnerability_scan")
def run_vulnerability_scan():
    from app.services.vulnerability_scanner import scan_all_repos
    scan_all_repos()

@celery_app.task(name="celery_app.run_cloud_cost_analysis")
def run_cloud_cost_analysis():
    from app.services.cloud_cost_optimizer import analyze_costs
    analyze_costs()

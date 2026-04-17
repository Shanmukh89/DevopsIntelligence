"""
Auditr — Celery Application
Background task queue for scheduled and async jobs.
"""

from celery import Celery
from app.core.config import settings

# Use the URL from settings, and append /1 for the results backend
base_redis_url = settings.REDIS_URL.rsplit('/', 1)[0] if '/' in settings.REDIS_URL[9:] else settings.REDIS_URL

broker_url = settings.REDIS_URL
backend_url = f"{base_redis_url}/1"

# Fix for Upstash rediss:// URLs which require ssl_cert_reqs parameter
if broker_url.startswith("rediss://") and "ssl_cert_reqs" not in broker_url:
    broker_url += "&ssl_cert_reqs=CERT_NONE" if "?" in broker_url else "?ssl_cert_reqs=CERT_NONE"

if backend_url.startswith("rediss://") and "ssl_cert_reqs" not in backend_url:
    backend_url += "&ssl_cert_reqs=CERT_NONE" if "?" in backend_url else "?ssl_cert_reqs=CERT_NONE"

celery_app = Celery(
    "auditr",
    broker=broker_url,
    backend=backend_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    broker_connection_retry_on_startup=True,
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

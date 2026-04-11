"""FastAPI dependencies (services, DB, settings)."""

from fastapi import Depends

from config import BaseAppSettings, get_settings
from database import get_db_session

# Database session dependency (use `Depends(get_db)` in routes)
get_db = get_db_session
from services.github_client import GitHubClient
from services.slack_client import SlackClient


def get_settings_dep() -> BaseAppSettings:
    return get_settings()


def get_github_client(
    settings: BaseAppSettings = Depends(get_settings_dep),
) -> GitHubClient:
    return GitHubClient(settings)


def get_slack_client(
    settings: BaseAppSettings = Depends(get_settings_dep),
) -> SlackClient:
    return SlackClient(settings)

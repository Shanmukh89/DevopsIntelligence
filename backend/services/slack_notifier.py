"""Send Auditr alerts to Slack (OAuth bot or webhook) with threading and updates."""

from __future__ import annotations

import json
import logging
import uuid
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from config import BaseAppSettings
from crypto import TokenEncryptionError, decrypt_secret_string, resolve_fernet_key
from models.builds import Build
from models.repositories import Repository
from models.slack_integration import SlackIntegration, SlackNotificationThread
from models.teams import Team
from models.vulnerabilities import VulnerabilityAlert
from services.slack_async_client import AsyncSlackClient
from services.slack_templates import (
    build_failure_message,
    cost_spike_message,
    log_anomaly_message,
    pr_review_message,
    vulnerability_message,
)
logger = logging.getLogger(__name__)


def _fernet_key(settings: BaseAppSettings) -> str:
    return resolve_fernet_key(
        fernet_key=settings.fernet_key,
        environment=settings.environment,
        jwt_secret_key=settings.jwt_secret_key,
    )


def _channel_for_feature(integration: SlackIntegration, feature: str) -> str:
    cfg = integration.channels_config or {}
    ch = cfg.get(feature) or integration.default_channel
    if not ch:
        return "#general"
    return ch


def _auditr_build_url(settings: BaseAppSettings, repo: Repository, build: Build) -> str:
    base = settings.auditr_dashboard_base_url.rstrip("/")
    return f"{base}/repos/{repo.id}/builds/{build.id}"


def _auditr_repo_url(settings: BaseAppSettings, repo: Repository) -> str:
    base = settings.auditr_dashboard_base_url.rstrip("/")
    return f"{base}/repos/{repo.id}"


def _github_build_url(repo_full_name: str, run_id: int | None) -> str | None:
    if not run_id:
        return f"https://github.com/{repo_full_name}"
    return f"https://github.com/{repo_full_name}/actions/runs/{run_id}"


def _github_pr_url(repo_full_name: str, pr_number: int) -> str:
    return f"https://github.com/{repo_full_name}/pull/{pr_number}"


class SlackNotifier:
    """High-level notifier with message coalescing via SlackNotificationThread."""

    def __init__(self, settings: BaseAppSettings, slack: AsyncSlackClient | None = None) -> None:
        self._settings = settings
        self._slack = slack or AsyncSlackClient()

    async def _get_integration(self, session: AsyncSession, team_id: uuid.UUID) -> SlackIntegration | None:
        r = await session.execute(select(SlackIntegration).where(SlackIntegration.team_id == team_id))
        return r.scalar_one_or_none()

    def _token(self, integration: SlackIntegration) -> str | None:
        if integration.integration_type == "webhook":
            return None
        if not integration.bot_token_encrypted:
            return None
        try:
            return decrypt_secret_string(integration.bot_token_encrypted, fernet_key=_fernet_key(self._settings))
        except TokenEncryptionError:
            logger.warning("slack_token_decrypt_failed team_id=%s", integration.team_id)
            return None

    async def _post_or_update(
        self,
        session: AsyncSession,
        integration: SlackIntegration,
        *,
        dedupe_key: str,
        channel: str,
        message_payload: dict[str, Any],
    ) -> None:
        """Post a new message or update an existing root message for the same dedupe key."""
        token = self._token(integration)
        if not token:
            await self._post_webhook(session, integration, message_payload)
            return

        existing = await session.execute(
            select(SlackNotificationThread).where(
                SlackNotificationThread.team_id == integration.team_id,
                SlackNotificationThread.dedupe_key == dedupe_key,
            )
        )
        row = existing.scalar_one_or_none()
        text = message_payload.get("text", "Auditr notification")
        attachments = message_payload.get("attachments")

        if row:
            res = await self._slack.chat_update(
                token,
                row.channel_id,
                ts=row.message_ts,
                text=text,
                attachments=attachments,
            )
            if not res.get("ok"):
                logger.warning("slack_chat_update_failed error=%s", res.get("error"))
            return

        res = await self._slack.chat_post_message(
            token,
            channel,
            text=text,
            attachments=attachments,
        )
        if not res.get("ok"):
            logger.warning("slack_chat_post_failed error=%s", res.get("error"))
            return
        ts = res.get("ts")
        ch = res.get("channel")
        if ts and ch:
            session.add(
                SlackNotificationThread(
                    team_id=integration.team_id,
                    slack_integration_id=integration.id,
                    dedupe_key=dedupe_key,
                    channel_id=str(ch),
                    message_ts=str(ts),
                )
            )

    async def _post_webhook(
        self,
        session: AsyncSession,
        integration: SlackIntegration,
        message_payload: dict[str, Any],
    ) -> None:
        if not integration.webhook_url_encrypted:
            return
        try:
            url = decrypt_secret_string(
                integration.webhook_url_encrypted,
                fernet_key=_fernet_key(self._settings),
            )
        except TokenEncryptionError:
            logger.warning("slack_webhook_decrypt_failed")
            return
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                r = await client.post(url, json=message_payload)
                if r.status_code >= 400:
                    logger.warning("slack_webhook_post_status=%s", r.status_code)
        except Exception:
            logger.warning("slack_webhook_post_failed", exc_info=False)

    async def notify_build_failure(
        self,
        session: AsyncSession,
        repo_id: uuid.UUID,
        build_id: uuid.UUID,
        explanation: str,
        so_results: list[dict[str, Any]] | dict[str, Any] | None,
    ) -> None:
        repo = await session.get(
            Repository,
            repo_id,
            options=[selectinload(Repository.team)],
        )
        build = await session.get(Build, build_id)
        if not repo or not build:
            logger.debug("notify_build_failure missing repo or build")
            return
        integration = await self._get_integration(session, repo.team_id)
        if not integration:
            return

        dedupe_key = f"build:{repo.id}:{build.commit_sha or str(build.id)}"
        channel = _channel_for_feature(integration, "builds")
        gh = _github_build_url(repo.full_name, build.github_run_id)
        auditr = _auditr_build_url(self._settings, repo, build)
        dismiss = f"dismiss|build|{repo.id}|{build.id}"
        payload = build_failure_message(
            repo_full_name=repo.full_name,
            build_label=f"Run `{build.github_run_id}` • `{build.branch}` • `{build.commit_sha[:7] if build.commit_sha else 'unknown'}`",
            explanation=explanation,
            so_results=so_results,
            github_url=gh,
            auditr_url=auditr,
            dismiss_value=dismiss,
            use_tracked_github_button=True,
            track_base_url=self._settings.api_public_base_url,
        )
        await self._post_or_update(session, integration, dedupe_key=dedupe_key, channel=channel, message_payload=payload)

    async def notify_pr_review(
        self,
        session: AsyncSession,
        repo_id: uuid.UUID,
        pr_id: int,
        issues: list[dict[str, Any]] | str,
    ) -> None:
        repo = await session.get(Repository, repo_id, options=[selectinload(Repository.team)])
        if not repo:
            return
        integration = await self._get_integration(session, repo.team_id)
        if not integration:
            return
        dedupe_key = f"pr:{repo.id}:{pr_id}"
        channel = _channel_for_feature(integration, "pr_reviews")
        gh = _github_pr_url(repo.full_name, pr_id)
        auditr = f"{self._settings.auditr_dashboard_base_url.rstrip('/')}/repos/{repo.id}/pulls/{pr_id}"
        dismiss = f"dismiss|pr|{repo.id}|{pr_id}"
        payload = pr_review_message(
            repo_full_name=repo.full_name,
            pr_number=pr_id,
            pr_title="Pull request",
            issues=issues,
            github_url=gh,
            auditr_url=auditr,
            dismiss_value=dismiss,
        )
        await self._post_or_update(session, integration, dedupe_key=dedupe_key, channel=channel, message_payload=payload)

    async def notify_vulnerability(
        self,
        session: AsyncSession,
        repo_id: uuid.UUID,
        alert: VulnerabilityAlert | dict[str, Any],
    ) -> None:
        if isinstance(alert, dict):
            pkg = str(alert.get("package_name", ""))
            sev = alert.get("severity")
            cve = alert.get("cve_id")
            desc = alert.get("description")
            alert_id = str(alert.get("id", ""))
        else:
            pkg = alert.package_name
            sev = alert.severity
            cve = alert.cve_id
            desc = alert.description
            alert_id = str(alert.id)

        repo = await session.get(Repository, repo_id, options=[selectinload(Repository.team)])
        if not repo:
            return
        integration = await self._get_integration(session, repo.team_id)
        if not integration:
            return
        dedupe_key = f"vuln:{repo.id}:{alert_id}"
        channel = _channel_for_feature(integration, "security")
        gh = f"https://github.com/{repo.full_name}/security/dependabot"
        auditr = _auditr_repo_url(self._settings, repo)
        dismiss = f"dismiss|vuln|{repo.id}|{alert_id}"
        payload = vulnerability_message(
            repo_full_name=repo.full_name,
            package_name=pkg,
            severity=sev,
            cve=cve,
            description=desc,
            github_url=gh,
            auditr_url=auditr,
            dismiss_value=dismiss,
        )
        await self._post_or_update(session, integration, dedupe_key=dedupe_key, channel=channel, message_payload=payload)

    async def notify_cost_spike(
        self,
        session: AsyncSession,
        team_id: uuid.UUID,
        savings_rec: dict[str, Any],
    ) -> None:
        team = await session.get(Team, team_id)
        integration = await self._get_integration(session, team_id)
        if not team or not integration:
            return
        dedupe_key = f"cost:{team.id}:{json.dumps(savings_rec, sort_keys=True)[:120]}"
        channel = _channel_for_feature(integration, "costs")
        auditr = f"{self._settings.auditr_dashboard_base_url.rstrip('/')}/teams/{team.id}/costs"
        dismiss = f"dismiss|cost|{team.id}|summary"
        payload = cost_spike_message(
            team_name=team.name,
            savings_rec=savings_rec,
            auditr_url=auditr,
            dismiss_value=dismiss,
        )
        await self._post_or_update(session, integration, dedupe_key=dedupe_key, channel=channel, message_payload=payload)

    async def notify_log_anomaly(
        self,
        session: AsyncSession,
        repo_id: uuid.UUID,
        summary: str,
    ) -> None:
        repo = await session.get(Repository, repo_id, options=[selectinload(Repository.team)])
        if not repo:
            return
        integration = await self._get_integration(session, repo.team_id)
        if not integration:
            return
        dedupe_key = f"log:{repo.id}:{hash(summary) % 10_000_000}"
        channel = _channel_for_feature(integration, "logs")
        gh = f"https://github.com/{repo.full_name}"
        auditr = _auditr_repo_url(self._settings, repo)
        dismiss = f"dismiss|log|{repo.id}|anomaly"
        payload = log_anomaly_message(
            repo_full_name=repo.full_name,
            summary=summary,
            github_url=gh,
            auditr_url=auditr,
            dismiss_value=dismiss,
        )
        await self._post_or_update(session, integration, dedupe_key=dedupe_key, channel=channel, message_payload=payload)

"""Slack Web API wrapper with graceful handling of missing channels."""

from __future__ import annotations

import logging
from typing import Any

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from config import BaseAppSettings

logger = logging.getLogger(__name__)


class SlackClient:
    """Thin wrapper around slack_sdk WebClient."""

    def __init__(self, settings: BaseAppSettings) -> None:
        self._settings = settings
        self._client: WebClient | None = None
        if settings.slack_bot_token:
            self._client = WebClient(token=settings.slack_bot_token)

    def _safe_call(self, fn_name: str, **kwargs: Any) -> dict[str, Any] | None:
        if not self._client:
            logger.debug("Slack not configured; skipping %s", fn_name)
            return None
        try:
            resp = getattr(self._client, fn_name)(**kwargs)
            if not resp.get("ok", False):
                logger.warning("Slack API returned not ok: %s", resp)
            return dict(resp) if isinstance(resp, dict) else {"data": resp}
        except SlackApiError as e:
            err = e.response.get("error", "") if e.response else ""
            if err in ("channel_not_found", "not_in_channel", "invalid_auth"):
                logger.warning("Slack %s — %s (kwargs keys=%s)", fn_name, err, list(kwargs.keys()))
                return None
            logger.exception("Slack API error in %s", fn_name)
            return None

    def post_message(self, channel: str | None, text: str, **kwargs: Any) -> dict[str, Any] | None:
        ch = channel or self._settings.slack_default_channel
        return self._safe_call("chat_postMessage", channel=ch, text=text, **kwargs)

    def post_thread_reply(
        self,
        channel: str | None,
        thread_ts: str,
        text: str,
        **kwargs: Any,
    ) -> dict[str, Any] | None:
        ch = channel or self._settings.slack_default_channel
        return self._safe_call(
            "chat_postMessage",
            channel=ch,
            thread_ts=thread_ts,
            text=text,
            **kwargs,
        )

    def upload_file(
        self,
        *,
        channels: str | None,
        content: bytes | None = None,
        filename: str | None = None,
        title: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any] | None:
        ch = channels or self._settings.slack_default_channel
        return self._safe_call(
            "files_upload_v2",
            channel=ch,
            content=content,
            filename=filename,
            title=title,
            **kwargs,
        )

"""Structured logging: JSON in production, readable in dev/test.

Named logging_config to avoid shadowing Python's standard library ``logging`` module.
"""

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any

from config import BaseAppSettings


class JsonFormatter(logging.Formatter):
    """Serialize log records as single-line JSON."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.now(tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        for key in ("request_id", "method", "path", "status_code", "duration_ms", "event_type", "action"):
            if hasattr(record, key):
                payload[key] = getattr(record, key)
        extra = getattr(record, "extra_data", None)
        if isinstance(extra, dict):
            payload["extra"] = extra
        return json.dumps(payload, default=str)


def setup_logging(settings: BaseAppSettings) -> None:
    """Configure root logger once."""
    root = logging.getLogger()
    root.handlers.clear()
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    root.setLevel(level)

    handler = logging.StreamHandler(sys.stdout)
    if settings.environment == "prod":
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s"),
        )
    root.addHandler(handler)

    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)

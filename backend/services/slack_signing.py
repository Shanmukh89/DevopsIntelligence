"""Verify Slack request signatures (Events API, interactivity)."""

from __future__ import annotations

import hashlib
import hmac
import time


def verify_slack_signature(
    *,
    signing_secret: str,
    body: bytes,
    timestamp_header: str | None,
    signature_header: str | None,
    max_age_seconds: int = 60 * 5,
) -> bool:
    """Verify `X-Slack-Request-Timestamp` + `X-Slack-Signature` (v0)."""
    if not signing_secret or not timestamp_header or not signature_header:
        return False
    try:
        ts = int(timestamp_header)
    except ValueError:
        return False
    if abs(int(time.time()) - ts) > max_age_seconds:
        return False
    sig_basestring = f"v0:{timestamp_header}:{body.decode('utf-8')}"
    my_sig = (
        "v0="
        + hmac.new(
            signing_secret.encode("utf-8"),
            sig_basestring.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
    )
    return hmac.compare_digest(my_sig, signature_header)

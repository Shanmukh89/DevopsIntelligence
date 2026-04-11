"""Parse structured LLM outputs with graceful handling of malformed or partial JSON."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, List, Tuple

_JSON_FENCE = re.compile(r"```(?:json)?\s*([\s\S]*?)```", re.IGNORECASE)


@dataclass
class Issue:
    """Structured issue extracted from a code review response."""

    severity: str | None = None
    category: str | None = None
    file_path: str | None = None
    line_number: int | None = None
    description: str | None = None
    suggestion: str | None = None


def extract_json_blob(text: str) -> str | None:
    """Pull JSON from markdown fences, or return stripped text if it looks like JSON."""
    if not text or not text.strip():
        return None
    m = _JSON_FENCE.search(text)
    if m:
        return m.group(1).strip()
    s = text.strip()
    if s.startswith("{") or s.startswith("["):
        return s
    return None


def parse_json_lenient(blob: str) -> Any | None:
    """Parse JSON; return None on failure."""
    try:
        return json.loads(blob)
    except json.JSONDecodeError:
        pass
    # Truncated object: try to salvage first complete array/object (best-effort)
    try:
        for opener, closer in (("[", "]"), ("{", "}")):
            if opener in blob:
                start = blob.index(opener)
                depth = 0
                for i, ch in enumerate(blob[start:], start=start):
                    if ch == opener:
                        depth += 1
                    elif ch == closer:
                        depth -= 1
                        if depth == 0:
                            return json.loads(blob[start : i + 1])
    except (json.JSONDecodeError, ValueError):
        return None
    return None


def parse_code_review_response(text: str) -> List[Issue]:
    """Extract issues from code review response (JSON list or {issues: [...]})."""
    raw = extract_json_blob(text) or text.strip()
    data = parse_json_lenient(raw) if raw else None
    if data is None:
        # Fallback: single free-text issue
        if text.strip():
            return [Issue(severity="info", description=text.strip()[:8000])]
        return []

    items: list[Any]
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        items = data.get("issues") or data.get("findings") or []
        if not isinstance(items, list):
            items = []
    else:
        return []

    out: list[Issue] = []
    for it in items:
        if isinstance(it, str):
            out.append(Issue(description=it))
            continue
        if not isinstance(it, dict):
            continue
        out.append(
            Issue(
                severity=_s(it.get("severity")),
                category=_s(it.get("category")),
                file_path=_s(it.get("file") or it.get("file_path")),
                line_number=_int(it.get("line") or it.get("line_number")),
                description=_s(it.get("description") or it.get("message")),
                suggestion=_s(it.get("suggestion") or it.get("fix")),
            ),
        )
    return out


def _s(v: Any) -> str | None:
    if v is None:
        return None
    return str(v) if str(v).strip() else None


def _int(v: Any) -> int | None:
    if v is None:
        return None
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def parse_sql_optimization_response(text: str) -> Tuple[str, str, str]:
    """
    Extract: optimized_query, explanation, create_index_statements.

    Missing parts become empty strings.
    """
    raw = extract_json_blob(text)
    if not raw:
        return "", text.strip(), ""

    data = parse_json_lenient(raw)
    if not isinstance(data, dict):
        return "", text.strip(), ""

    q = str(data.get("optimized_query") or data.get("query") or "").strip()
    expl = str(data.get("explanation") or data.get("summary") or "").strip()
    idx = data.get("create_index_statements")
    if isinstance(idx, list):
        idx_str = "\n".join(str(x) for x in idx)
    else:
        idx_str = str(idx or "").strip()
    return q, expl, idx_str


def parse_ci_explanation_response(text: str) -> dict[str, str]:
    """Normalize CI explanation to keys: root_cause, fix, verify."""
    raw = extract_json_blob(text)
    if raw:
        data = parse_json_lenient(raw)
        if isinstance(data, dict):
            return {
                "root_cause": str(data.get("root_cause", "")),
                "fix": str(data.get("fix", data.get("recommended_fix", ""))),
                "verify": str(data.get("verify", data.get("next_steps", ""))),
            }
    # Plain text → single blob
    return {"root_cause": text.strip(), "fix": "", "verify": ""}

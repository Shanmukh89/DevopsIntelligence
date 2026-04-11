"""Approximate token counts before sending to limit cost and truncation."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def estimate_tokens_for_text(text: str, model: str) -> int:
    """Approximate token count for a single string."""
    m = model.lower()
    if m.startswith("gpt") or m.startswith("o1") or m.startswith("o3"):
        try:
            import tiktoken

            try:
                enc = tiktoken.encoding_for_model(model)
            except KeyError:
                enc = tiktoken.get_encoding("cl100k_base")
            return len(enc.encode(text))
        except Exception as e:
            logger.debug("tiktoken_unavailable_fallback", extra={"reason": str(e)})
    # Claude and fallback: rough heuristic (~4 chars/token English)
    return max(1, len(text) // 4)


def estimate_messages_tokens(messages: list[dict[str, Any]], model: str) -> int:
    """Sum of estimated tokens for all message contents (plus small per-message overhead)."""
    total = 0
    for msg in messages:
        content = msg.get("content", "")
        if isinstance(content, list):
            # Multimodal: count text parts
            for part in content:
                if isinstance(part, dict) and part.get("type") == "text":
                    total += estimate_tokens_for_text(str(part.get("text", "")), model)
        else:
            total += estimate_tokens_for_text(str(content), model)
        total += 4  # role/metadata overhead
    return total


def truncate_messages_to_budget(
    messages: list[dict[str, Any]],
    model: str,
    max_input_tokens: int,
    *,
    reserve_output_tokens: int,
) -> list[dict[str, Any]]:
    """
    Shrink the last user message so input+reserve stays under max_input_tokens.
    Avoids provider hard truncation surprises on the tail of long prompts.
    """
    budget = max(256, max_input_tokens - reserve_output_tokens)
    current = estimate_messages_tokens(messages, model)
    if current <= budget:
        return messages

    # Copy and trim the last string content from the end
    out = [dict(m) for m in messages]
    for idx in range(len(out) - 1, -1, -1):
        content = out[idx].get("content", "")
        if isinstance(content, list):
            break
        if not isinstance(content, str):
            continue
        over = current - budget
        if over <= 0:
            break
        # Remove ~over tokens worth of characters from the start of the blob (keep tail context)
        chars_to_drop = min(len(content), over * 5)
        trimmed = content[chars_to_drop:]
        notice = "\n\n[... earlier content omitted to fit token budget ...]\n\n"
        out[idx]["content"] = notice + trimmed
        current = estimate_messages_tokens(out, model)
        break
    return out


def default_max_context_tokens(model: str) -> int:
    """Conservative context window cap for budgeting."""
    m = model.lower()
    if "gpt-4o" in m:
        return 128_000
    if "claude" in m:
        return 200_000
    return 128_000

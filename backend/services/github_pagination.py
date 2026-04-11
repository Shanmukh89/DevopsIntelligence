"""GitHub REST cursor / Link-header pagination helpers."""

from __future__ import annotations

import logging
import re
from typing import Any, Awaitable, Callable, TypeVar

import httpx

logger = logging.getLogger(__name__)

T = TypeVar("T")

_LINK_NEXT = re.compile(r'<([^>]+)>;\s*rel="next"')


def parse_next_url(link_header: str | None) -> str | None:
    if not link_header:
        return None
    m = _LINK_NEXT.search(link_header)
    return m.group(1) if m else None


async def fetch_all_pages_json(
    fetch_page: Callable[[str], Awaitable[httpx.Response]],
    first_url: str,
    *,
    max_items: int | None = None,
) -> list[dict[str, Any]]:
    """
    Follow `Link: ... rel="next"` until exhausted. Each successful page must be JSON array.
    """
    items: list[dict[str, Any]] = []
    url: str | None = first_url
    while url:
        resp = await fetch_page(url)
        if resp.status_code == 404:
            logger.info("github_pagination_404", extra={"url": url[:120]})
            break
        resp.raise_for_status()
        chunk = resp.json()
        if not isinstance(chunk, list):
            logger.warning("github_pagination_expected_array")
            break
        for row in chunk:
            items.append(row)
            if max_items is not None and len(items) >= max_items:
                return items
        url = parse_next_url(resp.headers.get("link"))
    return items

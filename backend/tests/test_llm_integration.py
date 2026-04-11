"""Tests for LLM client, prompts, parsing, caching, cost logging, and fallbacks."""

from __future__ import annotations

import json
import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from sqlalchemy import select

from services.llm.caching import LLMCache, cache_key_digest
from services.llm.client import LLMClient
from services.llm.cost_tracker import cost_by_feature, log_llm_cost, total_spend
from services.llm.prompts import prompt_ci_failure_explanation, prompt_code_review, prompt_sql_optimization
from services.llm.response_parser import parse_code_review_response, parse_sql_optimization_response
from services.llm.token_estimate import estimate_messages_tokens
from services.token_limiter import TeamTokenLimiter

from models.cost_logs import CostLog


def test_prompt_templates_structure():
    msgs = prompt_code_review("diff --git a\n+foo", "python")
    assert msgs[0]["role"] == "system"
    assert "code_review" in msgs[0]["content"] or "prompt:code_review" in msgs[0]["content"]
    assert "diff --git" in msgs[1]["content"]

    ci = prompt_ci_failure_explanation("ERROR: failed")
    assert len(ci) == 2
    assert "ERROR" in ci[1]["content"]

    sql = prompt_sql_optimization("SELECT 1", "Seq Scan")
    assert "SELECT 1" in sql[1]["content"]


def test_token_estimate_positive():
    m = [{"role": "user", "content": "hello world"}]
    n = estimate_messages_tokens(m, "gpt-4o")
    assert n > 0


def test_parse_code_review_json_and_malformed():
    text = """```json
[{"severity": "high", "description": "bug", "file_path": "a.py", "line_number": 1}]
```"""
    issues = parse_code_review_response(text)
    assert len(issues) == 1
    assert issues[0].severity == "high"
    assert issues[0].file_path == "a.py"

    bad = parse_code_review_response("not json at all but ")
    assert len(bad) >= 1
    assert bad[0].description


def test_parse_sql_optimization():
    body = json.dumps(
        {
            "optimized_query": "SELECT 2",
            "explanation": "faster",
            "create_index_statements": "CREATE INDEX ix ON t(a);",
        },
    )
    q, e, idx = parse_sql_optimization_response(f"```json\n{body}\n```")
    assert "SELECT 2" in q
    assert "faster" in e
    assert "CREATE INDEX" in idx


@pytest.mark.asyncio
async def test_llm_cache_key_stable():
    msgs = [{"role": "user", "content": "x"}]
    a = cache_key_digest("gpt-4o", msgs, 0.7)
    b = cache_key_digest("gpt-4o", msgs, 0.7)
    assert a == b
    c = cache_key_digest("gpt-4o", msgs, 0.8)
    assert a != c


@pytest.mark.asyncio
async def test_call_llm_uses_cache_second_hit():
    cache = MagicMock(spec=LLMCache)
    cache.get_cached_response = AsyncMock(side_effect=[None, "cached-body"])
    cache.set_cached_response = AsyncMock()
    cache.ttl_for_kind = MagicMock(return_value=3600)
    cache.close = AsyncMock()

    oai_body = {
        "choices": [{"message": {"content": "fresh"}}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5},
    }

    transport = httpx.MockTransport(
        lambda r: httpx.Response(
            200,
            json=oai_body,
        ),
    )
    async with httpx.AsyncClient(transport=transport) as http:
        with patch.dict(
            "os.environ",
            {"OPENAI_API_KEY": "sk-test-openai", "ANTHROPIC_API_KEY": "sk-test-anthropic"},
            clear=False,
        ):
            from config import clear_settings_cache
            from config.llm_config import clear_llm_config_cache

            clear_settings_cache()
            clear_llm_config_cache()

            client = LLMClient(http_client=http, cache=cache)
            m = [{"role": "user", "content": "ping"}]
            r1 = await client.call_llm("gpt-4o", m, use_cache=True)
            assert r1.text == "fresh"
            r2 = await client.call_llm("gpt-4o", m, use_cache=True)
            assert r2.text == "cached-body"
            assert cache.set_cached_response.await_count == 1
            await client.aclose()


@pytest.mark.asyncio
async def test_fallback_openai_to_anthropic():
    cache = MagicMock(spec=LLMCache)
    cache.get_cached_response = AsyncMock(return_value=None)
    cache.set_cached_response = AsyncMock()
    cache.ttl_for_kind = MagicMock(return_value=3600)
    cache.close = AsyncMock()

    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.host)
        if "openai.com" in str(request.url):
            return httpx.Response(500, json={"error": "server"})
        if "anthropic.com" in str(request.url):
            return httpx.Response(
                200,
                json={
                    "content": [{"type": "text", "text": "from-claude"}],
                    "usage": {"input_tokens": 3, "output_tokens": 2},
                },
            )
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http:
        with patch.dict(
            "os.environ",
            {"OPENAI_API_KEY": "sk-test", "ANTHROPIC_API_KEY": "ant-test"},
            clear=False,
        ):
            from config import clear_settings_cache
            from config.llm_config import clear_llm_config_cache

            clear_settings_cache()
            clear_llm_config_cache()

            client = LLMClient(http_client=http, cache=cache)
            r = await client.call_llm("gpt-4o", [{"role": "user", "content": "hi"}], use_cache=False)
            assert r.text == "from-claude"
            assert "api.openai.com" in str(calls)
            assert "api.anthropic.com" in str(calls)
            await client.aclose()


@pytest.mark.asyncio
async def test_log_llm_cost_persists(db_session, sample_team):
    row = await log_llm_cost(
        db_session,
        tokens_used=100,
        model="gpt-4o",
        feature="code_review",
        input_tokens=60,
        output_tokens=40,
        team_id=sample_team.id,
        cached=False,
    )
    await db_session.commit()
    assert row.cost_in_usd >= Decimal("0")
    res = await db_session.execute(select(CostLog).where(CostLog.team_id == sample_team.id))
    rows = res.scalars().all()
    assert len(rows) == 1

    total = await total_spend(db_session, team_id=sample_team.id)
    assert total >= Decimal("0")

    by_f = await cost_by_feature(db_session, team_id=sample_team.id)
    assert any(x["feature"] == "code_review" for x in by_f)


@pytest.mark.asyncio
async def test_token_limiter_blocks_expensive_when_over_budget(monkeypatch):
    monkeypatch.setenv("DEFAULT_MONTHLY_TEAM_TOKEN_BUDGET", "10")
    from config import clear_settings_cache
    from config.llm_config import clear_llm_config_cache

    clear_settings_cache()
    clear_llm_config_cache()

    limiter = TeamTokenLimiter(redis_url="redis://localhost:6379/15")
    mock_redis = AsyncMock()
    mock_redis.incrby = AsyncMock(return_value=11)
    mock_redis.get = AsyncMock(return_value="11")
    mock_redis.expire = AsyncMock(return_value=True)
    mock_redis.aclose = AsyncMock()
    limiter._get_client = AsyncMock(return_value=mock_redis)  # noqa: SLF001

    tid = uuid.uuid4()
    allowed = await limiter.is_feature_allowed(tid, "code_review")
    assert allowed is False

    cheap = await limiter.is_feature_allowed(tid, "ci_failure_explanation")
    assert cheap is True

    await limiter.close()

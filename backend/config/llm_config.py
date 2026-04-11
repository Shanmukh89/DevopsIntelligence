"""LLM provider configuration: models, defaults, rate limits, and feature routing."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Literal

FeatureName = Literal[
    "code_review",
    "ci_failure_explanation",
    "documentation",
    "sql_optimization",
    "vulnerability_triage",
    "codebase_qa",
    "clone_detection",
    "dependency_advice",
    "incident_summary",
]


@dataclass(frozen=True)
class ProviderRateLimit:
    """Requests per minute and tokens per minute (provider-enforced ceilings for our scheduler)."""

    requests_per_minute: int
    tokens_per_minute: int


@dataclass(frozen=True)
class LLMRuntimeConfig:
    """Runtime LLM settings loaded from environment."""

    openai_api_key: str = ""
    anthropic_api_key: str = ""

    default_temperature: float = 0.7
    default_max_tokens: int = 2000
    request_timeout_seconds: float = 30.0

    # Primary model IDs (must match provider APIs)
    openai_default_model: str = "gpt-4o"
    anthropic_default_model: str = "claude-sonnet-4-20250514"

    # Fallback when primary provider errors (HTTP 5xx, timeout, etc.)
    fallback_openai_model: str = "gpt-4o"
    fallback_anthropic_model: str = "claude-sonnet-4-20250514"

    rate_limits_openai: ProviderRateLimit = field(
        default_factory=lambda: ProviderRateLimit(requests_per_minute=500, tokens_per_minute=150_000),
    )
    rate_limits_anthropic: ProviderRateLimit = field(
        default_factory=lambda: ProviderRateLimit(requests_per_minute=400, tokens_per_minute=120_000),
    )

    # Per-feature defaults (model id string as accepted by call_llm)
    feature_models: dict[str, str] = field(
        default_factory=lambda: {
            "code_review": "gpt-4o",
            "ci_failure_explanation": "gpt-4o",
            "documentation": "gpt-4o",
            "sql_optimization": "gpt-4o",
            "vulnerability_triage": "claude-sonnet-4-20250514",
            "codebase_qa": "gpt-4o",
            "clone_detection": "gpt-4o",
            "dependency_advice": "gpt-4o",
            "incident_summary": "claude-sonnet-4-20250514",
        },
    )

    # Per-team monthly token budget (0 = unlimited)
    default_monthly_team_token_budget: int = 0

    warn_budget_ratio: float = 0.8
    embedding_openai_model: str = "text-embedding-3-small"
    embedding_hf_model: str = "sentence-transformers/all-MiniLM-L6-v2"


@lru_cache
def get_llm_config() -> LLMRuntimeConfig:
    """Cached LLM config from application settings and env."""
    from config import get_settings

    s = get_settings()
    return LLMRuntimeConfig(
        openai_api_key=s.openai_api_key,
        anthropic_api_key=s.anthropic_api_key,
        default_monthly_team_token_budget=int(os.getenv("DEFAULT_MONTHLY_TEAM_TOKEN_BUDGET", "0")),
    )


def clear_llm_config_cache() -> None:
    """Clear cached LLM config (for tests)."""
    get_llm_config.cache_clear()


def model_provider(model: str) -> Literal["openai", "anthropic"]:
    """Infer API provider from model id."""
    m = model.lower()
    if m.startswith("gpt") or m.startswith("o1") or m.startswith("o3"):
        return "openai"
    if "claude" in m:
        return "anthropic"
    # Safe default for unknown ids
    return "openai"


def fallback_chain_for_model(model: str) -> list[str]:
    """Ordered list of model ids to try (primary first, then alternate provider)."""
    cfg = get_llm_config()
    primary = model
    if model_provider(primary) == "openai":
        return [primary, cfg.fallback_anthropic_model]
    return [primary, cfg.fallback_openai_model]

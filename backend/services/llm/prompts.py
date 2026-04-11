"""Versioned prompt templates (v1) for LLM features — A/B testing via PROMPT_VERSION_* env overrides."""

from __future__ import annotations

import os
from typing import Any

# Bump when changing instructions; pair with experiments / A/B buckets.
PROMPT_VERSION_DEFAULT = "v1"


def _pv(name: str) -> str:
    return os.getenv(name, PROMPT_VERSION_DEFAULT)


def _banner(feature: str, version: str) -> str:
    return f"[prompt:{feature}:{version}]"


def prompt_code_review(diff: str, language: str) -> list[dict[str, Any]]:
    """Return system + user messages for PR code review."""
    v = _pv("PROMPT_VERSION_CODE_REVIEW")
    system = (
        f"{_banner('code_review', v)} You are an expert code reviewer. "
        "Focus on correctness, security, performance, and maintainability. "
        "Respond with structured JSON when asked for machine parsing; otherwise be concise."
    )
    user = (
        f"Language: {language}\n\n"
        "Review this unified diff. List concrete issues with severity, file, line when possible.\n\n"
        f"{diff}"
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def prompt_ci_failure_explanation(log_tail: str) -> list[dict[str, Any]]:
    """Explain what went wrong in a CI failure."""
    v = _pv("PROMPT_VERSION_CI_FAILURE")
    system = (
        f"{_banner('ci_failure', v)} You are a senior CI/CD engineer. "
        "Explain failures clearly: root cause, likely fix, and what to verify next."
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": f"CI log tail:\n```\n{log_tail}\n```"},
    ]


def prompt_documentation(source_code: str, language: str) -> list[dict[str, Any]]:
    """Generate documentation for a function or module."""
    v = _pv("PROMPT_VERSION_DOCS")
    system = (
        f"{_banner('documentation', v)} You write clear API documentation. "
        "Include summary, parameters, returns, raises, and example if helpful."
    )
    return [
        {"role": "system", "content": system},
        {
            "role": "user",
            "content": f"Language: {language}\n\nGenerate documentation for:\n```\n{source_code}\n```",
        },
    ]


def prompt_sql_optimization(query: str, explain_output: str) -> list[dict[str, Any]]:
    """Suggest optimizations for a slow SQL query."""
    v = _pv("PROMPT_VERSION_SQL")
    system = (
        f"{_banner('sql_optimization', v)} You are a database performance expert. "
        "Respond with JSON containing: optimized_query, explanation, create_index_statements (string or list)."
    )
    return [
        {"role": "system", "content": system},
        {
            "role": "user",
            "content": (
                f"Original query:\n```sql\n{query}\n```\n\n"
                f"EXPLAIN output:\n```\n{explain_output}\n```"
            ),
        },
    ]


def prompt_vulnerability_triage(
    package_name: str,
    version: str,
    advisory_text: str,
) -> list[dict[str, Any]]:
    """Triage a dependency vulnerability advisory."""
    v = _pv("PROMPT_VERSION_VULN")
    system = (
        f"{_banner('vulnerability_triage', v)} You are an application security engineer. "
        "Summarize impact, affected components, and recommended remediation."
    )
    return [
        {"role": "system", "content": system},
        {
            "role": "user",
            "content": (
                f"Package: {package_name}@{version}\n\nAdvisory:\n{advisory_text}"
            ),
        },
    ]


def prompt_codebase_qa(question: str, context_chunks: str) -> list[dict[str, Any]]:
    """Answer a question using retrieved code chunks (RAG)."""
    v = _pv("PROMPT_VERSION_CODEBASE_QA")
    system = (
        f"{_banner('codebase_qa', v)} You answer questions about a codebase using only the provided context. "
        "If context is insufficient, say what is missing."
    )
    return [
        {"role": "system", "content": system},
        {
            "role": "user",
            "content": f"Context:\n{context_chunks}\n\nQuestion: {question}",
        },
    ]


def prompt_clone_detection(snippet_a: str, snippet_b: str) -> list[dict[str, Any]]:
    """Compare two snippets for clone / duplication analysis."""
    v = _pv("PROMPT_VERSION_CLONE")
    system = (
        f"{_banner('clone_detection', v)} You analyze code similarity. "
        "Describe overlap, refactoring opportunities, and risk of duplication."
    )
    return [
        {"role": "system", "content": system},
        {
            "role": "user",
            "content": f"Snippet A:\n```\n{snippet_a}\n```\n\nSnippet B:\n```\n{snippet_b}\n```",
        },
    ]


def prompt_dependency_advice(
    manifest_excerpt: str,
    outdated_report: str,
) -> list[dict[str, Any]]:
    """Suggest safe dependency upgrades."""
    v = _pv("PROMPT_VERSION_DEPS")
    system = (
        f"{_banner('dependency_advice', v)} You are a dependency management expert. "
        "Prioritize security and compatibility; call out breaking changes."
    )
    return [
        {"role": "system", "content": system},
        {
            "role": "user",
            "content": f"Manifest excerpt:\n{manifest_excerpt}\n\nOutdated report:\n{outdated_report}",
        },
    ]


def prompt_incident_summary(events_text: str) -> list[dict[str, Any]]:
    """Summarize incident timeline from logs or events."""
    v = _pv("PROMPT_VERSION_INCIDENT")
    system = (
        f"{_banner('incident_summary', v)} You are an SRE. Produce a tight timeline, "
        "customer impact, blast radius, and immediate mitigations."
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": f"Events:\n{events_text}"},
    ]

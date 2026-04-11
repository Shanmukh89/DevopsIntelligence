# Prompting guide

This document describes LLM prompt templates in `backend/services/llm/prompts.py`, how they are versioned, and how to change them safely.

## Prompt inventory (v1)

| Feature | Function | Purpose |
|--------|------------|---------|
| PR code review | `prompt_code_review(diff, language)` | Review unified diffs with severity-aware feedback |
| CI failure | `prompt_ci_failure_explanation(log_tail)` | Explain CI logs and suggest fixes |
| Documentation | `prompt_documentation(source_code, language)` | Generate docstrings / API docs |
| SQL performance | `prompt_sql_optimization(query, explain_output)` | Suggest query + index changes (JSON-shaped output) |
| Vulnerability triage | `prompt_vulnerability_triage(package_name, version, advisory_text)` | Summarize impact and remediation |
| Codebase Q&A | `prompt_codebase_qa(question, context_chunks)` | RAG-style answers from retrieved chunks |
| Clone detection | `prompt_clone_detection(snippet_a, snippet_b)` | Duplication and refactor hints |
| Dependencies | `prompt_dependency_advice(manifest_excerpt, outdated_report)` | Upgrade path with risk notes |
| Incident summary | `prompt_incident_summary(events_text)` | Timeline, impact, mitigations |

Each system prompt embeds a short banner like `[prompt:<feature>:v1]` so logs and traces can correlate responses with a **prompt version**.

## Design decisions

1. **Separation of concerns**: Prompts return plain OpenAI-style `messages` lists only. Provider choice, temperature, caching, and cost logging live in `LLMClient` and `cost_tracker`, not in prompt functions.

2. **Structured outputs**: Features that need machine parsing (e.g. SQL optimization) instruct the model to emit JSON. Parsing is centralized in `response_parser.py` with fence extraction and lenient JSON recovery.

3. **Token safety**: `token_estimate.py` approximates tokens before the request and can trim oversized user content to reduce surprise truncation and cost.

4. **Caching**: Responses are cached in Redis keyed by `hash(model + messages + temperature)` (see `caching.cache_key_digest`). Long-lived analysis uses a 7-day TTL; realtime features use 1 hour.

5. **Secrets**: API keys are loaded from `OPENAI_API_KEY` and `ANTHROPIC_API_KEY` via `config` settings. They must never appear in logs; cost logs store only model, feature, tokens, and USD estimate.

## Modifying prompts

1. **Bump the version** in the banner (e.g. `v1` → `v2`) or add a `PROMPT_VERSION_<FEATURE>` environment variable override (see `prompts.py`).

2. **Keep JSON contracts stable** where parsers exist (`parse_code_review_response`, `parse_sql_optimization_response`). If the schema changes, update parsers and tests together.

3. **Run tests**: `pytest tests/test_llm_integration.py` from the `backend` directory.

4. **Prefer small, testable changes**: Adjust tone or add constraints in the system message before growing user payloads.

## A/B testing strategy

1. **Environment flags**: Each feature can read `PROMPT_VERSION_<NAME>` (e.g. `PROMPT_VERSION_CODE_REVIEW=v2`) to switch templates without code deploys, when wired to the same functions.

2. **Buckets**: In production, assign teams or repositories to version A/B via configuration (e.g. `RepositoryConfig.settings`) and pass the chosen version into prompt builders or set env per worker.

3. **Metrics**: Compare `cost_by_feature` and qualitative signals (issues found, user thumbs) per prompt version. Store the banner prefix in application logs to join LLM outputs with spend.

4. **Rollout**: Ship v2 to a small percentage of traffic, monitor cost and error rates, then expand.

## Related code

- `backend/config/llm_config.py` — default models per feature, timeouts, rate-limit metadata  
- `backend/services/llm/client.py` — `call_llm`, `stream_llm`, fallback, 30s timeout  
- `backend/services/llm/caching.py` — Redis cache and repo-scoped invalidation  
- `backend/services/llm/cost_tracker.py` — `cost_logs` rows and dashboard aggregates  

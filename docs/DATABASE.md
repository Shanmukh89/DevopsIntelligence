# Auditr database schema

PostgreSQL 15 hosts the primary application data. The [`pgvector`](https://github.com/pgvector/pgvector) extension stores OpenAI-sized embeddings (`vector(1536)`) for codebase RAG and similarity features.

## Connection

- Configure `DATABASE_URL` for the FastAPI app (async), e.g. `postgresql+asyncpg://user:pass@host:5432/auditr`.
- Alembic and `seeds.py` use a sync URL derived automatically: `postgresql+asyncpg://` → `postgresql+psycopg2://`.

## Migrations

From the `backend/` directory:

```bash
python -m alembic upgrade head
```

| Revision       | File                              | Purpose |
|----------------|-----------------------------------|---------|
| `001_initial`  | `migration_001_initial_tables.py` | Core tables; `code_embeddings` without vector column |
| `002_pgvector` | `migration_002_pgvector_extension.py` | `CREATE EXTENSION vector`; add `embedding` column |
| `003_indexes`  | `migration_003_indexes.py`        | IVFFlat cosine index, partial uniques, partial status indexes |

## Entity relationship (ASCII)

```
┌─────────────┐       ┌─────────────────┐       ┌──────────────────┐
│   teams     │       │  repositories   │       │ repository_configs│
│─────────────│       │─────────────────│       │──────────────────│
│ id (PK)     │──┐    │ id (PK)         │──┐    │ id (PK)          │
│ name        │  └──<│ team_id (FK)    │  └──<│ repository_id(U) │
│ created_at  │       │ github_repo_id│*      │ settings (JSONB) │
│ updated_at  │       │ full_name       │       └──────────────────┘
│ deleted_at  │       │ ...             │
└─────────────┘       └────────┬────────┘
       ^                       │
       │              ┌────────┴──────────────────────────────────────────┐
       │              │        │                                          │
┌──────┴──────┐  ┌────▼───────────┐  ┌─────────────┐  ┌─────────────────┐
│ team_members│  │ code_embeddings│  │  pr_reviews │  │     builds      │
│ team_id(FK) │  │ embedding ◆    │  │  repo_id    │  │  repo_id        │
└─────────────┘  │ chunk_text     │  └──────┬──────┘  │ stackoverflow   │
┌─────────────┐  └────────────────┘         │         │ _results (JSONB)│
│team_api_keys│                             ▼         └────────┬────────┘
└─────────────┘                      ┌──────────────┐            │
                                     │  pr_issues   │     ┌────▼────────┐
                                     └──────────────┘     │ build_logs  │
┌─────────────────┐                                       └─────────────┘
│ cloud_cost_     │
│ recommendations │◄── teams.id
│ cost_data       │
│ (JSONB)         │
└─────────────────┘

◆ = pgvector `vector(1536)` + IVFFlat `vector_cosine_ops` index (see below)

Other tables: `vulnerability_alerts`, `code_clones`, `generated_documentation`, `webhook_events`.
```

## Conventions

- **Primary keys:** UUID v4 (`uuid.uuid4` in Python; `Uuid` columns in SQLAlchemy).
- **Timestamps:** naive UTC via `datetime.utcnow()` on `created_at` / `updated_at`.
- **Soft delete:** `deleted_at` on tenant-scoped entities where history should be retained.
- **Flexible payloads:** JSONB for `stackoverflow_results`, `cost_data`, webhook payloads, and repository settings.

## Indexes (PRD-aligned)

| Index | Purpose |
|-------|---------|
| `uq_repositories_github_repo_id` | Unique GitHub repository id per row |
| `uq_vulnerability_alerts_repository_cve` | Unique `(repository_id, cve_id)` where `cve_id IS NOT NULL` |
| `ix_code_embeddings_embedding_ivfflat` | IVFFlat index on `embedding` with **`vector_cosine_ops`** (cosine distance / similarity) |
| `ix_vulnerability_alerts_open_by_repo` | Partial index: `status = 'open'` |
| `ix_cloud_cost_recommendations_open_by_team` | Partial index: `status = 'open'` |

**Note:** pgvector does not use GiST for the `vector` type; approximate search uses **IVFFlat** or **HNSW**. This schema follows the PRD’s IVFFlat + cosine operators pattern.

## Local seed data

```bash
cd backend
python seeds.py
```

Creates a demo team, member, repository, and one `code_embeddings` row (zero vector) for smoke testing.

## ORM layout

| Module | Models |
|--------|--------|
| `models/teams.py` | `Team`, `TeamMember`, `TeamAPIKey` |
| `models/repositories.py` | `Repository`, `RepositoryConfig` |
| `models/code_embeddings.py` | `CodeEmbedding` |
| `models/pr_reviews.py` | `PRReview`, `PRIssue` |
| `models/builds.py` | `Build`, `BuildLog` |
| `models/vulnerabilities.py` | `VulnerabilityAlert` |
| `models/code_clones.py` | `CodeClone` |
| `models/costs.py` | `CloudCostRecommendation` |
| `models/documentation.py` | `GeneratedDocumentation` |
| `models/webhook_event.py` | `WebhookEvent` |

Shared bases live in `database.py`: `Base`, `BaseModel` (`id`, `created_at`, `updated_at`), and `SoftDeleteMixin` (`deleted_at`) in `models/teams.py`.

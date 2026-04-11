"""Indexes: IVFFlat cosine on embeddings, partial uniques, active-status partial indexes.

Revision ID: 003_indexes
Revises: 002_pgvector
Create Date: 2026-04-12

Note: pgvector uses IVFFlat/HNSW — not GiST. IVFFlat with vector_cosine_ops matches
the PRD and supports cosine similarity search.

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003_indexes"
down_revision: Union[str, None] = "002_pgvector"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Replace non-unique CVE lookup index with partial unique (repository + CVE)
    op.drop_index("ix_vulnerability_alerts_cve_id", table_name="vulnerability_alerts")
    op.create_index(
        "uq_vulnerability_alerts_repository_cve",
        "vulnerability_alerts",
        ["repository_id", "cve_id"],
        unique=True,
        postgresql_where=sa.text("cve_id IS NOT NULL"),
    )

    # IVFFlat index for cosine similarity (pgvector)
    op.execute(
        sa.text(
            """
            CREATE INDEX ix_code_embeddings_embedding_ivfflat
            ON code_embeddings
            USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 100);
            """
        )
    )

    # Partial indexes for "active" rows (open alerts / open recommendations)
    op.create_index(
        "ix_vulnerability_alerts_open_by_repo",
        "vulnerability_alerts",
        ["repository_id"],
        unique=False,
        postgresql_where=sa.text("status = 'open'"),
    )
    op.create_index(
        "ix_cloud_cost_recommendations_open_by_team",
        "cloud_cost_recommendations",
        ["team_id"],
        unique=False,
        postgresql_where=sa.text("status = 'open'"),
    )


def downgrade() -> None:
    op.drop_index(
        "ix_cloud_cost_recommendations_open_by_team",
        table_name="cloud_cost_recommendations",
    )
    op.drop_index(
        "ix_vulnerability_alerts_open_by_repo",
        table_name="vulnerability_alerts",
    )
    op.execute(sa.text("DROP INDEX IF EXISTS ix_code_embeddings_embedding_ivfflat"))
    op.drop_index("uq_vulnerability_alerts_repository_cve", table_name="vulnerability_alerts")
    op.create_index(
        "ix_vulnerability_alerts_cve_id",
        "vulnerability_alerts",
        ["cve_id"],
        unique=False,
    )

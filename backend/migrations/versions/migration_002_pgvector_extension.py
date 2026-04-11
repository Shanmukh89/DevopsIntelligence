"""Enable pgvector and add embedding column to code_embeddings.

Revision ID: 002_pgvector
Revises: 001_initial
Create Date: 2026-04-12

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

revision: str = "002_pgvector"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(sa.text("CREATE EXTENSION IF NOT EXISTS vector"))
    op.add_column(
        "code_embeddings",
        sa.Column("embedding", Vector(1536), nullable=True),
    )
    op.execute(sa.text("ALTER TABLE code_embeddings ALTER COLUMN embedding SET NOT NULL"))


def downgrade() -> None:
    op.drop_column("code_embeddings", "embedding")
    op.execute(sa.text("DROP EXTENSION IF EXISTS vector"))

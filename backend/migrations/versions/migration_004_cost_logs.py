"""LLM cost_logs table for API spend auditing.

Revision ID: 004_cost_logs
Revises: 003_indexes
Create Date: 2026-04-12

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "004_cost_logs"
down_revision: Union[str, None] = "003_indexes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "cost_logs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("tokens_used", sa.BigInteger(), nullable=False),
        sa.Column("cost_in_usd", sa.Numeric(14, 6), nullable=False),
        sa.Column("model", sa.String(length=128), nullable=False),
        sa.Column("feature", sa.String(length=64), nullable=False),
        sa.Column("repo_id", sa.Uuid(), nullable=True),
        sa.Column("team_id", sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(["repo_id"], ["repositories.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cost_logs")),
    )
    op.create_index(op.f("ix_cost_logs_model"), "cost_logs", ["model"], unique=False)
    op.create_index(op.f("ix_cost_logs_feature"), "cost_logs", ["feature"], unique=False)
    op.create_index(op.f("ix_cost_logs_repo_id"), "cost_logs", ["repo_id"], unique=False)
    op.create_index(op.f("ix_cost_logs_team_id"), "cost_logs", ["team_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_cost_logs_team_id"), table_name="cost_logs")
    op.drop_index(op.f("ix_cost_logs_repo_id"), table_name="cost_logs")
    op.drop_index(op.f("ix_cost_logs_feature"), table_name="cost_logs")
    op.drop_index(op.f("ix_cost_logs_model"), table_name="cost_logs")
    op.drop_table("cost_logs")

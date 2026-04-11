"""Initial schema: teams, repos, builds, PRs, alerts, docs (no vector column yet).

Revision ID: 001_initial
Revises:
Create Date: 2026-04-12

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "teams",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_teams")),
    )
    op.create_table(
        "webhook_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("event_type", sa.String(length=128), nullable=False),
        sa.Column("delivery_id", sa.String(length=128), nullable=True),
        sa.Column("action", sa.String(length=64), nullable=True),
        sa.Column("repository_full_name", sa.String(length=255), nullable=True),
        sa.Column("payload_summary", sa.Text(), nullable=True),
        sa.Column("payload_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("processing_note", sa.String(length=512), nullable=True),
        sa.Column("received_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_webhook_events")),
    )
    op.create_index(op.f("ix_webhook_events_delivery_id"), "webhook_events", ["delivery_id"], unique=False)
    op.create_index(op.f("ix_webhook_events_event_type"), "webhook_events", ["event_type"], unique=False)

    op.create_table(
        "team_members",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("team_id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("github_login", sa.String(length=100), nullable=True),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_team_members")),
        sa.UniqueConstraint("team_id", "email", name="uq_team_members_team_email"),
    )
    op.create_index(op.f("ix_team_members_team_id"), "team_members", ["team_id"], unique=False)

    op.create_table(
        "team_api_keys",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("team_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("key_prefix", sa.String(length=16), nullable=False),
        sa.Column("key_hash", sa.String(length=128), nullable=False),
        sa.Column("last_used_at", sa.DateTime(), nullable=True),
        sa.Column("scopes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_team_api_keys")),
    )
    op.create_index(op.f("ix_team_api_keys_team_id"), "team_api_keys", ["team_id"], unique=False)

    op.create_table(
        "cloud_cost_recommendations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("team_id", sa.Uuid(), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=True),
        sa.Column("resource_id", sa.String(length=255), nullable=True),
        sa.Column("resource_type", sa.String(length=100), nullable=True),
        sa.Column("current_cost_monthly", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("potential_saving", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("recommendation", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("cost_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("detected_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cloud_cost_recommendations")),
    )
    op.create_index(
        op.f("ix_cloud_cost_recommendations_team_id"),
        "cloud_cost_recommendations",
        ["team_id"],
        unique=False,
    )

    op.create_table(
        "repositories",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("team_id", sa.Uuid(), nullable=False),
        sa.Column("github_repo_id", sa.BigInteger(), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("default_branch", sa.String(length=100), nullable=False),
        sa.Column("webhook_secret", sa.String(length=255), nullable=True),
        sa.Column("last_indexed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_repositories")),
        sa.UniqueConstraint("github_repo_id", name="uq_repositories_github_repo_id"),
    )
    op.create_index(op.f("ix_repositories_team_id"), "repositories", ["team_id"], unique=False)

    op.create_table(
        "repository_configs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("repository_id", sa.Uuid(), nullable=False),
        sa.Column("settings", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["repository_id"], ["repositories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_repository_configs")),
        sa.UniqueConstraint("repository_id", name="uq_repository_configs_repository_id"),
    )

    op.create_table(
        "code_embeddings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("repository_id", sa.Uuid(), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("start_line", sa.Integer(), nullable=False),
        sa.Column("end_line", sa.Integer(), nullable=False),
        sa.Column("chunk_text", sa.Text(), nullable=False),
        sa.Column("language", sa.String(length=50), nullable=True),
        sa.Column("last_updated", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["repository_id"], ["repositories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_code_embeddings")),
    )
    op.create_index(op.f("ix_code_embeddings_repository_id"), "code_embeddings", ["repository_id"], unique=False)

    op.create_table(
        "pr_reviews",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("repository_id", sa.Uuid(), nullable=False),
        sa.Column("pr_number", sa.Integer(), nullable=False),
        sa.Column("pr_title", sa.String(length=500), nullable=True),
        sa.Column("author_github_login", sa.String(length=100), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=True),
        sa.Column("issues_count", sa.Integer(), nullable=False),
        sa.Column("review_body", sa.Text(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["repository_id"], ["repositories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_pr_reviews")),
    )
    op.create_index(op.f("ix_pr_reviews_repository_id"), "pr_reviews", ["repository_id"], unique=False)

    op.create_table(
        "pr_issues",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("pr_review_id", sa.Uuid(), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=True),
        sa.Column("category", sa.String(length=50), nullable=True),
        sa.Column("file_path", sa.String(length=500), nullable=True),
        sa.Column("line_number", sa.Integer(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("suggestion", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["pr_review_id"], ["pr_reviews.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_pr_issues")),
    )
    op.create_index(op.f("ix_pr_issues_pr_review_id"), "pr_issues", ["pr_review_id"], unique=False)

    op.create_table(
        "builds",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("repository_id", sa.Uuid(), nullable=False),
        sa.Column("github_run_id", sa.BigInteger(), nullable=True),
        sa.Column("branch", sa.String(length=100), nullable=True),
        sa.Column("commit_sha", sa.String(length=40), nullable=True),
        sa.Column("author_github_login", sa.String(length=100), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=True),
        sa.Column("ai_explanation", sa.Text(), nullable=True),
        sa.Column("stackoverflow_results", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["repository_id"], ["repositories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_builds")),
        sa.UniqueConstraint("github_run_id", name="uq_builds_github_run_id"),
    )
    op.create_index(op.f("ix_builds_repository_id"), "builds", ["repository_id"], unique=False)

    op.create_table(
        "build_logs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("build_id", sa.Uuid(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("line_text", sa.Text(), nullable=False),
        sa.Column("log_level", sa.String(length=32), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["build_id"], ["builds.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_build_logs")),
    )
    op.create_index(op.f("ix_build_logs_build_id"), "build_logs", ["build_id"], unique=False)

    op.create_table(
        "vulnerability_alerts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("repository_id", sa.Uuid(), nullable=False),
        sa.Column("package_name", sa.String(length=255), nullable=False),
        sa.Column("installed_version", sa.String(length=100), nullable=True),
        sa.Column("patched_version", sa.String(length=100), nullable=True),
        sa.Column("cve_id", sa.String(length=50), nullable=True),
        sa.Column("ghsa_id", sa.String(length=50), nullable=True),
        sa.Column("severity", sa.String(length=20), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("detected_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["repository_id"], ["repositories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_vulnerability_alerts")),
    )
    op.create_index(
        op.f("ix_vulnerability_alerts_repository_id"),
        "vulnerability_alerts",
        ["repository_id"],
        unique=False,
    )
    op.create_index(op.f("ix_vulnerability_alerts_cve_id"), "vulnerability_alerts", ["cve_id"], unique=False)

    op.create_table(
        "code_clones",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("repository_id", sa.Uuid(), nullable=False),
        sa.Column("file_path_a", sa.String(length=500), nullable=True),
        sa.Column("start_line_a", sa.Integer(), nullable=True),
        sa.Column("file_path_b", sa.String(length=500), nullable=True),
        sa.Column("start_line_b", sa.Integer(), nullable=True),
        sa.Column("similarity_score", sa.Float(), nullable=True),
        sa.Column("detected_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["repository_id"], ["repositories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_code_clones")),
    )
    op.create_index(op.f("ix_code_clones_repository_id"), "code_clones", ["repository_id"], unique=False)

    op.create_table(
        "generated_documentation",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("repository_id", sa.Uuid(), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("symbol_name", sa.String(length=255), nullable=True),
        sa.Column("doc_content", sa.Text(), nullable=False),
        sa.Column("language", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["repository_id"], ["repositories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_generated_documentation")),
    )
    op.create_index(
        op.f("ix_generated_documentation_repository_id"),
        "generated_documentation",
        ["repository_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_table("generated_documentation")
    op.drop_table("code_clones")
    op.drop_table("vulnerability_alerts")
    op.drop_table("build_logs")
    op.drop_table("builds")
    op.drop_table("pr_issues")
    op.drop_table("pr_reviews")
    op.drop_table("code_embeddings")
    op.drop_table("repository_configs")
    op.drop_table("repositories")
    op.drop_table("cloud_cost_recommendations")
    op.drop_table("team_api_keys")
    op.drop_table("team_members")
    op.drop_table("webhook_events")
    op.drop_table("teams")

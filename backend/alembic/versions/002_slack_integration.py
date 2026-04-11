"""slack integration tables

Revision ID: 002_slack
Revises: 001_webhook
Create Date: 2026-04-12

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002_slack"
down_revision: Union[str, None] = "001_webhook"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "slack_integrations",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("team_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("workspace_id", sa.String(length=32), nullable=True),
        sa.Column("workspace_name", sa.String(length=255), nullable=True),
        sa.Column("integration_type", sa.String(length=32), nullable=False),
        sa.Column("bot_token_encrypted", sa.Text(), nullable=True),
        sa.Column("webhook_url_encrypted", sa.Text(), nullable=True),
        sa.Column("default_channel", sa.String(length=128), nullable=True),
        sa.Column("channels_config", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("team_id", name="uq_slack_integrations_team_id"),
    )
    op.create_index("ix_slack_integrations_team_id", "slack_integrations", ["team_id"], unique=False)
    op.create_index("ix_slack_integrations_workspace_id", "slack_integrations", ["workspace_id"], unique=False)

    op.create_table(
        "slack_notification_threads",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("team_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("slack_integration_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("dedupe_key", sa.String(length=512), nullable=False),
        sa.Column("channel_id", sa.String(length=32), nullable=False),
        sa.Column("message_ts", sa.String(length=32), nullable=False),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["slack_integration_id"], ["slack_integrations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("team_id", "dedupe_key", name="uq_slack_threads_team_dedupe"),
    )
    op.create_index("ix_slack_notification_threads_team_id", "slack_notification_threads", ["team_id"], unique=False)
    op.create_index("ix_slack_notification_threads_dedupe_key", "slack_notification_threads", ["dedupe_key"], unique=False)
    op.create_index(
        "ix_slack_notification_threads_slack_integration_id",
        "slack_notification_threads",
        ["slack_integration_id"],
        unique=False,
    )

    op.create_table(
        "slack_alert_dismissals",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("team_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("alert_kind", sa.String(length=64), nullable=False),
        sa.Column("alert_ref", sa.String(length=512), nullable=False),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("team_id", "alert_kind", "alert_ref", name="uq_slack_dismissals_ref"),
    )
    op.create_index("ix_slack_alert_dismissals_team_id", "slack_alert_dismissals", ["team_id"], unique=False)
    op.create_index("ix_slack_alert_dismissals_alert_ref", "slack_alert_dismissals", ["alert_ref"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_slack_alert_dismissals_alert_ref", table_name="slack_alert_dismissals")
    op.drop_index("ix_slack_alert_dismissals_team_id", table_name="slack_alert_dismissals")
    op.drop_table("slack_alert_dismissals")
    op.drop_index("ix_slack_notification_threads_slack_integration_id", table_name="slack_notification_threads")
    op.drop_index("ix_slack_notification_threads_dedupe_key", table_name="slack_notification_threads")
    op.drop_index("ix_slack_notification_threads_team_id", table_name="slack_notification_threads")
    op.drop_table("slack_notification_threads")
    op.drop_index("ix_slack_integrations_workspace_id", table_name="slack_integrations")
    op.drop_index("ix_slack_integrations_team_id", table_name="slack_integrations")
    op.drop_table("slack_integrations")

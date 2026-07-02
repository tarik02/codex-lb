"""add openai-compatible account provider fields

Revision ID: 20260701_000000_add_openai_compatible_accounts
Revises: 20260701_000000_add_weekly_pace_smoothing_minutes
Create Date: 2026-07-01 00:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine import Connection

revision = "20260701_000000_add_openai_compatible_accounts"
down_revision = "20260701_000000_add_weekly_pace_smoothing_minutes"
branch_labels = None
depends_on = None


def _columns(connection: Connection, table_name: str) -> set[str]:
    inspector = sa.inspect(connection)
    if not inspector.has_table(table_name):
        return set()
    return {str(column["name"]) for column in inspector.get_columns(table_name) if column.get("name") is not None}


def upgrade() -> None:
    bind = op.get_bind()
    columns = _columns(bind, "accounts")
    if not columns:
        return
    with op.batch_alter_table("accounts") as batch_op:
        if "provider" not in columns:
            batch_op.add_column(
                sa.Column("provider", sa.String(), nullable=False, server_default=sa.text("'chatgpt'"))
            )
        if "provider_base_url" not in columns:
            batch_op.add_column(sa.Column("provider_base_url", sa.String(), nullable=True))
        if "provider_model_prefix" not in columns:
            batch_op.add_column(sa.Column("provider_model_prefix", sa.String(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    columns = _columns(bind, "accounts")
    with op.batch_alter_table("accounts") as batch_op:
        if "provider_model_prefix" in columns:
            batch_op.drop_column("provider_model_prefix")
        if "provider_base_url" in columns:
            batch_op.drop_column("provider_base_url")
        if "provider" in columns:
            batch_op.drop_column("provider")

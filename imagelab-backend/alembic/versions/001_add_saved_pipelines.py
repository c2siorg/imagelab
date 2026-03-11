"""add saved_pipelines table

Revision ID: 001
Revises:
Create Date: 2026-03-11 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "saved_pipelines",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.String(length=1000), nullable=False, server_default=""),
        sa.Column("pipeline_json", sa.Text(), nullable=False),
        sa.Column("workspace_state", sa.Text(), nullable=False, server_default=""),
        sa.Column("share_token", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("share_token"),
    )
    op.create_index(op.f("ix_saved_pipelines_name"), "saved_pipelines", ["name"], unique=False)
    op.create_index(op.f("ix_saved_pipelines_share_token"), "saved_pipelines", ["share_token"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_saved_pipelines_share_token"), table_name="saved_pipelines")
    op.drop_index(op.f("ix_saved_pipelines_name"), table_name="saved_pipelines")
    op.drop_table("saved_pipelines")

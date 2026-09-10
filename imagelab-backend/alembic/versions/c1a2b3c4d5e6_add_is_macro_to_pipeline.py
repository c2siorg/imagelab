"""add is_macro to pipeline table

Revision ID: c1a2b3c4d5e6
Revises: f78ce0d472f1
Create Date: 2026-07-28 22:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c1a2b3c4d5e6"
down_revision: str | None = "f78ce0d472f1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "pipeline",
        sa.Column("is_macro", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )


def downgrade() -> None:
    op.drop_column("pipeline", "is_macro")

"""fix pipeline_shares token_hash uniqueness

Revision ID: f78ce0d472f1
Revises: b323f95e8c19
Create Date: 2026-07-13 00:19:31.476665

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f78ce0d472f1"
down_revision: str | None = "b323f95e8c19"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_index(op.f("ix_pipeline_shares_token_hash"), table_name="pipeline_shares")
    op.create_index(
        op.f("ix_pipeline_shares_token_hash"),
        "pipeline_shares",
        ["token_hash"],
        unique=False,  # <-- set to whatever the review actually asked for
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_pipeline_shares_token_hash"), table_name="pipeline_shares")
    op.create_index(
        op.f("ix_pipeline_shares_token_hash"),
        "pipeline_shares",
        ["token_hash"],
        unique=True,  # revert to the original merged state
    )

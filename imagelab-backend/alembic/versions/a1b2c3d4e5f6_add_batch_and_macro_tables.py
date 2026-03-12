"""add_batch_and_macro_tables

Revision ID: a1b2c3d4e5f6
Revises:
Create Date: 2026-03-12 14:40:00.000000

Adds three new tables for Feature 4 (Batch Processing) and
Feature 5 (Custom Composite Operators / Macros):

  batchjob       — one row per batch run submitted via POST /api/batch/execute
  batchitemresult — one row per image in a batch, updated as images complete
  macro           — one row per saved composite operator definition
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # batchjob
    # ------------------------------------------------------------------
    op.create_table(
        "batchjob",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("pending", "running", "completed", "failed", name="jobstatus"),
            nullable=False,
        ),
        sa.Column("total_images", sa.Integer(), nullable=False),
        sa.Column("completed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("image_format", sa.String(), nullable=False, server_default="png"),
        sa.Column("pipeline_steps", sa.JSON(), nullable=True),
        sa.Column("error", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # ------------------------------------------------------------------
    # batchitemresult
    # ------------------------------------------------------------------
    op.create_table(
        "batchitemresult",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("job_id", sa.Uuid(), nullable=False),
        sa.Column("image_index", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("pending", "processing", "success", "failed", name="itemstatus"),
            nullable=False,
        ),
        sa.Column("result_image_b64", sa.Text(), nullable=True),
        sa.Column("error", sa.String(), nullable=True),
        sa.Column("duration_ms", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(["job_id"], ["batchjob.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_batchitemresult_job_id", "batchitemresult", ["job_id"])

    # ------------------------------------------------------------------
    # macro
    # ------------------------------------------------------------------
    op.create_table(
        "macro",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("steps", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_macro_name", "macro", ["name"])


def downgrade() -> None:
    op.drop_index("ix_macro_name", table_name="macro")
    op.drop_table("macro")
    op.drop_index("ix_batchitemresult_job_id", table_name="batchitemresult")
    op.drop_table("batchitemresult")
    op.drop_table("batchjob")
    # Drop enums (PostgreSQL requires explicit cleanup)
    op.execute("DROP TYPE IF EXISTS jobstatus")
    op.execute("DROP TYPE IF EXISTS itemstatus")

"""Immutable approval proposals and publication recovery evidence."""

import sqlalchemy as sa
from alembic import op

revision = "0008_github_publications"
down_revision = "0007_github_resolution_runs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "github_publications",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column(
            "run_id",
            sa.String(32),
            sa.ForeignKey("github_resolution_runs.id", ondelete="RESTRICT"),
            unique=True,
            nullable=False,
        ),
        sa.Column("plan", sa.JSON(), nullable=False),
        sa.Column("plan_hash", sa.String(64), nullable=False),
        sa.Column("approved_hash", sa.String(64), nullable=True),
        sa.Column("state", sa.String(24), nullable=False),
        sa.Column("outcome", sa.JSON(), nullable=False),
        sa.Column("last_error", sa.String(64), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "state IN ('awaiting_approval','approved','publishing','retry_needed','published','stale')",
            name="ck_github_publication_state",
        ),
    )


def downgrade() -> None:
    op.drop_table("github_publications")

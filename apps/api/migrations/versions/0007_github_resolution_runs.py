"""Persist bound controlled resolution results and failures."""

import sqlalchemy as sa
from alembic import op

revision = "0007_github_resolution_runs"
down_revision = "0006_github_issue_snapshots"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "github_resolution_runs",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column(
            "binding_id",
            sa.BigInteger(),
            sa.ForeignKey("github_issue_snapshots.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("state", sa.String(16), nullable=False),
        sa.Column("result", sa.JSON(), nullable=True),
        sa.Column("result_hash", sa.String(64), nullable=True),
        sa.Column("failure", sa.String(64), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "state IN ('running', 'completed', 'failed')", name="ck_github_run_state"
        ),
    )
    op.create_index(
        "ix_github_resolution_runs_binding_id", "github_resolution_runs", ["binding_id"]
    )


def downgrade() -> None:
    op.drop_table("github_resolution_runs")

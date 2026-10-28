"""Persist immutable GitHub Issue/commit/Snapshot provenance."""

import sqlalchemy as sa
from alembic import op

revision = "0006_github_issue_snapshots"
down_revision = "0005_structural_index"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "github_issue_snapshots",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column("remote_repository_id", sa.BigInteger(), nullable=False),
        sa.Column("repository_full_name", sa.String(255), nullable=False),
        sa.Column("commit_sha", sa.String(40), nullable=False),
        sa.Column("issue_number", sa.Integer(), nullable=False),
        sa.Column("profile", sa.String(32), nullable=False),
        sa.Column("issue_body", sa.Text(), nullable=False),
        sa.Column("issue_body_hash", sa.String(64), nullable=False),
        sa.Column(
            "snapshot_id",
            sa.BigInteger(),
            sa.ForeignKey("repository_snapshots.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("audit", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "remote_repository_id",
            "commit_sha",
            "issue_number",
            name="uq_github_issue_commit",
        ),
        sa.CheckConstraint(
            "remote_repository_id > 0 AND issue_number > 0",
            name="ck_github_issue_identity",
        ),
        sa.CheckConstraint(
            "length(commit_sha) = 40 AND length(issue_body_hash) = 64",
            name="ck_github_binding_hashes",
        ),
    )
    op.create_index(
        "ix_github_issue_snapshots_snapshot_id",
        "github_issue_snapshots",
        ["snapshot_id"],
    )


def downgrade() -> None:
    op.drop_table("github_issue_snapshots")

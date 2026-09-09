"""Add code-aware chunks.

Revision ID: 0003_add_code_chunks
Revises: 0002_add_repository_ingestion
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_add_code_chunks"
down_revision: str | Sequence[str] | None = "0002_add_repository_ingestion"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "repository_snapshots",
        sa.Column("chunk_count", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column(
        "repository_snapshots",
        sa.Column("chunking_version", sa.String(length=64), nullable=True),
    )
    op.create_table(
        "code_chunks",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("snapshot_id", sa.BigInteger(), nullable=False),
        sa.Column("snapshot_file_id", sa.BigInteger(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("language", sa.String(length=32), nullable=False),
        sa.Column("chunk_type", sa.String(length=32), nullable=False),
        sa.Column("symbol_name", sa.Text(), nullable=True),
        sa.Column("qualified_name", sa.Text(), nullable=True),
        sa.Column("parent_symbol", sa.Text(), nullable=True),
        sa.Column("start_line", sa.Integer(), nullable=False),
        sa.Column("end_line", sa.Integer(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("chunking_version", sa.String(length=64), nullable=False),
        sa.Column("raw_content", sa.Text(), nullable=False),
        sa.Column("embedding_content", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["snapshot_file_id"], ["snapshot_files.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["snapshot_id"], ["repository_snapshots.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "snapshot_file_id",
            "sequence",
            "chunking_version",
            name="uq_code_chunks_file_sequence_version",
        ),
    )
    op.create_index(
        op.f("ix_code_chunks_snapshot_file_id"),
        "code_chunks",
        ["snapshot_file_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_code_chunks_snapshot_id"),
        "code_chunks",
        ["snapshot_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_code_chunks_snapshot_id"), table_name="code_chunks")
    op.drop_index(op.f("ix_code_chunks_snapshot_file_id"), table_name="code_chunks")
    op.drop_table("code_chunks")
    op.drop_column("repository_snapshots", "chunking_version")
    op.drop_column("repository_snapshots", "chunk_count")

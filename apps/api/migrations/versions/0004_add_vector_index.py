"""Add configured vector indexing fields.

Revision ID: 0004_add_vector_index
Revises: 0003_add_code_chunks
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

revision: str = "0004_add_vector_index"
down_revision: str | Sequence[str] | None = "0003_add_code_chunks"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "repository_snapshots",
        sa.Column("embedding_provider", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "repository_snapshots",
        sa.Column("embedding_model", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "repository_snapshots",
        sa.Column("embedding_dimensions", sa.Integer(), nullable=True),
    )
    op.add_column(
        "repository_snapshots",
        sa.Column("indexed_chunk_count", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column(
        "repository_snapshots",
        sa.Column("indexed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column("code_chunks", sa.Column("embedding", Vector(dim=512), nullable=True))
    op.add_column(
        "code_chunks",
        sa.Column("embedding_provider", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "code_chunks",
        sa.Column("embedding_model", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "code_chunks",
        sa.Column("embedded_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("code_chunks", "embedded_at")
    op.drop_column("code_chunks", "embedding_model")
    op.drop_column("code_chunks", "embedding_provider")
    op.drop_column("code_chunks", "embedding")
    op.drop_column("repository_snapshots", "indexed_at")
    op.drop_column("repository_snapshots", "indexed_chunk_count")
    op.drop_column("repository_snapshots", "embedding_dimensions")
    op.drop_column("repository_snapshots", "embedding_model")
    op.drop_column("repository_snapshots", "embedding_provider")

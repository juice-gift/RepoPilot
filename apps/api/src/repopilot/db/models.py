from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    JSON,
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Identity,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Repository(Base):
    __tablename__ = "repositories"

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    local_path: Mapped[str] = mapped_column(Text, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    snapshots: Mapped[list["RepositorySnapshot"]] = relationship(
        back_populates="repository", cascade="all, delete-orphan"
    )


class RepositorySnapshot(Base):
    __tablename__ = "repository_snapshots"
    __table_args__ = (
        UniqueConstraint(
            "repository_id", "content_hash", name="uq_snapshots_repository_hash"
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    repository_id: Mapped[int] = mapped_column(
        ForeignKey("repositories.id", ondelete="CASCADE"), index=True
    )
    content_hash: Mapped[str] = mapped_column(String(64))
    source_revision: Mapped[str | None] = mapped_column(String(255), nullable=True)
    accepted_file_count: Mapped[int] = mapped_column(Integer)
    skipped_file_count: Mapped[int] = mapped_column(Integer)
    total_bytes: Mapped[int] = mapped_column(BigInteger)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    chunking_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    structural_index_version: Mapped[str | None] = mapped_column(
        String(64), nullable=True
    )
    embedding_provider: Mapped[str | None] = mapped_column(String(64), nullable=True)
    embedding_model: Mapped[str | None] = mapped_column(String(255), nullable=True)
    embedding_dimensions: Mapped[int | None] = mapped_column(Integer, nullable=True)
    indexed_chunk_count: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0"
    )
    indexed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    repository: Mapped[Repository] = relationship(back_populates="snapshots")
    files: Mapped[list["SnapshotFile"]] = relationship(
        back_populates="snapshot", cascade="all, delete-orphan"
    )


class GitHubIssueSnapshot(Base):
    """Immutable external provenance; identical source at two commits stays distinct."""

    __tablename__ = "github_issue_snapshots"
    __table_args__ = (
        UniqueConstraint(
            "remote_repository_id",
            "commit_sha",
            "issue_number",
            name="uq_github_issue_commit",
        ),
        CheckConstraint(
            "remote_repository_id > 0 AND issue_number > 0",
            name="ck_github_issue_identity",
        ),
        CheckConstraint(
            "length(commit_sha) = 40 AND length(issue_body_hash) = 64",
            name="ck_github_binding_hashes",
        ),
    )
    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    remote_repository_id: Mapped[int] = mapped_column(BigInteger)
    repository_full_name: Mapped[str] = mapped_column(String(255))
    commit_sha: Mapped[str] = mapped_column(String(40))
    issue_number: Mapped[int] = mapped_column(Integer)
    profile: Mapped[str] = mapped_column(String(32))
    issue_body: Mapped[str] = mapped_column(Text)
    issue_body_hash: Mapped[str] = mapped_column(String(64))
    snapshot_id: Mapped[int] = mapped_column(
        ForeignKey("repository_snapshots.id", ondelete="CASCADE"), index=True
    )
    audit: Mapped[dict[str, object]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class SnapshotFile(Base):
    __tablename__ = "snapshot_files"
    __table_args__ = (
        UniqueConstraint("snapshot_id", "path", name="uq_snapshot_files_path"),
        UniqueConstraint("snapshot_id", "id", name="uq_snapshot_files_snapshot_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    snapshot_id: Mapped[int] = mapped_column(
        ForeignKey("repository_snapshots.id", ondelete="CASCADE"), index=True
    )
    path: Mapped[str] = mapped_column(Text)
    language: Mapped[str] = mapped_column(String(32))
    content_hash: Mapped[str] = mapped_column(String(64))
    byte_size: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text)

    snapshot: Mapped[RepositorySnapshot] = relationship(back_populates="files")
    chunks: Mapped[list["CodeChunk"]] = relationship(
        back_populates="snapshot_file", cascade="all, delete-orphan"
    )


class CodeChunk(Base):
    __tablename__ = "code_chunks"
    __table_args__ = (
        UniqueConstraint(
            "snapshot_file_id",
            "sequence",
            "chunking_version",
            name="uq_code_chunks_file_sequence_version",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    snapshot_id: Mapped[int] = mapped_column(
        ForeignKey("repository_snapshots.id", ondelete="CASCADE"), index=True
    )
    snapshot_file_id: Mapped[int] = mapped_column(
        ForeignKey("snapshot_files.id", ondelete="CASCADE"), index=True
    )
    sequence: Mapped[int] = mapped_column(Integer)
    language: Mapped[str] = mapped_column(String(32))
    chunk_type: Mapped[str] = mapped_column(String(32))
    symbol_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    qualified_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    parent_symbol: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_line: Mapped[int] = mapped_column(Integer)
    end_line: Mapped[int] = mapped_column(Integer)
    content_hash: Mapped[str] = mapped_column(String(64))
    chunking_version: Mapped[str] = mapped_column(String(64))
    raw_content: Mapped[str] = mapped_column(Text)
    embedding_content: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(512), nullable=True)
    embedding_provider: Mapped[str | None] = mapped_column(String(64), nullable=True)
    embedding_model: Mapped[str | None] = mapped_column(String(255), nullable=True)
    embedded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    snapshot_file: Mapped[SnapshotFile] = relationship(back_populates="chunks")


class CodeSymbol(Base):
    __tablename__ = "code_symbols"
    __table_args__ = (
        UniqueConstraint(
            "snapshot_id", "index_version", "id", name="uq_symbols_snapshot_version_id"
        ),
        ForeignKeyConstraint(
            ["snapshot_id", "snapshot_file_id"],
            ["snapshot_files.snapshot_id", "snapshot_files.id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["snapshot_id", "index_version", "parent_symbol_id"],
            [
                "code_symbols.snapshot_id",
                "code_symbols.index_version",
                "code_symbols.id",
            ],
            ondelete="CASCADE",
        ),
        CheckConstraint(
            "start_line > 0 AND end_line >= start_line", name="ck_symbols_location"
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    snapshot_id: Mapped[int] = mapped_column(
        ForeignKey("repository_snapshots.id", ondelete="CASCADE"), index=True
    )
    snapshot_file_id: Mapped[int] = mapped_column(BigInteger, index=True)
    index_version: Mapped[str] = mapped_column(String(64))
    language: Mapped[str] = mapped_column(String(32))
    kind: Mapped[str] = mapped_column(String(32))
    name: Mapped[str] = mapped_column(Text, index=True)
    normalized_name: Mapped[str] = mapped_column(Text, index=True)
    qualified_name: Mapped[str] = mapped_column(Text, index=True)
    parent_symbol_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    start_line: Mapped[int] = mapped_column(Integer)
    end_line: Mapped[int] = mapped_column(Integer)


class ImportRelation(Base):
    __tablename__ = "import_relations"
    __table_args__ = (
        ForeignKeyConstraint(
            ["snapshot_id", "snapshot_file_id"],
            ["snapshot_files.snapshot_id", "snapshot_files.id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["snapshot_id", "target_file_id"],
            ["snapshot_files.snapshot_id", "snapshot_files.id"],
            ondelete="CASCADE",
        ),
        CheckConstraint(
            "status IN ('resolved', 'unresolved', 'ambiguous')",
            name="ck_imports_status",
        ),
        CheckConstraint(
            "(status = 'resolved' AND target_file_id IS NOT NULL) OR (status != 'resolved' AND target_file_id IS NULL)",
            name="ck_imports_target",
        ),
        CheckConstraint("line > 0 AND column_number > 0", name="ck_imports_location"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    snapshot_id: Mapped[int] = mapped_column(
        ForeignKey("repository_snapshots.id", ondelete="CASCADE"), index=True
    )
    snapshot_file_id: Mapped[int] = mapped_column(BigInteger, index=True)
    index_version: Mapped[str] = mapped_column(String(64))
    module: Mapped[str] = mapped_column(Text)
    imported_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    alias: Mapped[str | None] = mapped_column(Text, nullable=True)
    level: Mapped[int] = mapped_column(Integer)
    line: Mapped[int] = mapped_column(Integer)
    column_number: Mapped[int] = mapped_column(Integer)
    target_file_id: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True, index=True
    )
    status: Mapped[str] = mapped_column(String(16))
    reason: Mapped[str] = mapped_column(Text)


class CodeReference(Base):
    __tablename__ = "code_references"
    __table_args__ = (
        ForeignKeyConstraint(
            ["snapshot_id", "snapshot_file_id"],
            ["snapshot_files.snapshot_id", "snapshot_files.id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["snapshot_id", "index_version", "target_symbol_id"],
            [
                "code_symbols.snapshot_id",
                "code_symbols.index_version",
                "code_symbols.id",
            ],
            ondelete="CASCADE",
        ),
        CheckConstraint(
            "status IN ('resolved', 'unresolved', 'ambiguous')",
            name="ck_references_status",
        ),
        CheckConstraint(
            "(status = 'resolved' AND target_symbol_id IS NOT NULL) OR (status != 'resolved' AND target_symbol_id IS NULL)",
            name="ck_references_target",
        ),
        CheckConstraint(
            "line > 0 AND column_number > 0", name="ck_references_location"
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    snapshot_id: Mapped[int] = mapped_column(
        ForeignKey("repository_snapshots.id", ondelete="CASCADE"), index=True
    )
    snapshot_file_id: Mapped[int] = mapped_column(BigInteger, index=True)
    index_version: Mapped[str] = mapped_column(String(64))
    name: Mapped[str] = mapped_column(Text)
    qualifier: Mapped[str | None] = mapped_column(Text, nullable=True)
    line: Mapped[int] = mapped_column(Integer)
    column_number: Mapped[int] = mapped_column(Integer)
    target_symbol_id: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True, index=True
    )
    status: Mapped[str] = mapped_column(String(16), index=True)
    reason: Mapped[str] = mapped_column(Text)

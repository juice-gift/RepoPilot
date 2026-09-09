from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from repopilot.db.models import Repository, RepositorySnapshot, SnapshotFile
from repopilot.ingestion.scanner import (
    ScanResult,
    calculate_snapshot_hash,
    scan_repository,
)


@dataclass(frozen=True)
class IngestionResult:
    repository: Repository
    snapshot: RepositorySnapshot
    scan: ScanResult
    snapshot_created: bool


def ingest_repository(
    session: Session,
    *,
    requested_path: str,
    allowed_root: Path,
    repository_name: str | None = None,
) -> IngestionResult:
    scan = scan_repository(requested_path, allowed_root)
    local_path = str(scan.repository_path)
    repository = session.scalar(
        select(Repository).where(Repository.local_path == local_path)
    )
    if repository is None:
        repository = Repository(
            name=repository_name or scan.repository_path.name,
            local_path=local_path,
        )
        session.add(repository)
        session.flush()
    elif repository_name is not None and repository.name != repository_name:
        repository.name = repository_name

    snapshot_hash = calculate_snapshot_hash(scan.files)
    snapshot = session.scalar(
        select(RepositorySnapshot).where(
            RepositorySnapshot.repository_id == repository.id,
            RepositorySnapshot.content_hash == snapshot_hash,
        )
    )
    snapshot_created = snapshot is None
    if snapshot is None:
        snapshot = RepositorySnapshot(
            repository_id=repository.id,
            content_hash=snapshot_hash,
            source_revision=None,
            accepted_file_count=len(scan.files),
            skipped_file_count=len(scan.skipped_files),
            total_bytes=scan.total_bytes,
        )
        session.add(snapshot)
        session.flush()
        session.add_all(
            SnapshotFile(
                snapshot_id=snapshot.id,
                path=file.path,
                language=file.language,
                content_hash=file.content_hash,
                byte_size=file.byte_size,
                content=file.content,
            )
            for file in scan.files
        )

    session.commit()
    session.refresh(repository)
    session.refresh(snapshot)
    return IngestionResult(
        repository=repository,
        snapshot=snapshot,
        scan=scan,
        snapshot_created=snapshot_created,
    )

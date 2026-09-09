from collections.abc import Iterator
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from repopilot.api.dependencies import get_database_session
from repopilot.chunking.chunker import CHUNKING_VERSION
from repopilot.chunking.service import ChunkingResult
from repopilot.config import Settings
from repopilot.main import create_app


def create_test_client(session: Session, allowed_root: Path) -> TestClient:
    settings = Settings(
        database_url="postgresql+psycopg://user:password@localhost/database",
        repository_allowed_root=allowed_root,
        _env_file=None,
    )
    app = create_app(settings=settings)

    def override_database_session() -> Iterator[Session]:
        yield session

    app.dependency_overrides[get_database_session] = override_database_session
    return TestClient(app)


def test_create_snapshot_chunks_returns_inspectable_metadata(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    snapshot = SimpleNamespace(chunking_version=CHUNKING_VERSION)
    chunk = SimpleNamespace(
        id=5,
        snapshot_id=2,
        snapshot_file_id=3,
        sequence=0,
        language="python",
        chunk_type="function",
        symbol_name="answer",
        qualified_name="answer",
        parent_symbol=None,
        start_line=1,
        end_line=2,
        content_hash="a" * 64,
        chunking_version=CHUNKING_VERSION,
        raw_content="def answer():\n    return 42\n",
        embedding_content="File: app.py\nSource:\ndef answer():\n    return 42\n",
    )
    monkeypatch.setattr(
        "repopilot.api.routes.chunks.chunk_snapshot",
        lambda *args, **kwargs: ChunkingResult(snapshot, (chunk,), True),
    )
    file = SimpleNamespace(id=3, path="app.py")
    scalar_result = MagicMock()
    scalar_result.all.return_value = [file]
    session = MagicMock(spec=Session)
    session.scalars.return_value = scalar_result

    with create_test_client(session, tmp_path) as client:
        response = client.post("/api/repositories/1/snapshots/2/chunks")

    assert response.status_code == 200
    assert response.json()["chunk_count"] == 1
    assert response.json()["chunks_created"] is True
    assert response.json()["chunks"][0] == {
        "id": 5,
        "snapshot_id": 2,
        "file_path": "app.py",
        "sequence": 0,
        "language": "python",
        "chunk_type": "function",
        "symbol_name": "answer",
        "qualified_name": "answer",
        "parent_symbol": None,
        "start_line": 1,
        "end_line": 2,
        "content_hash": "a" * 64,
        "chunking_version": CHUNKING_VERSION,
        "raw_content": "def answer():\n    return 42\n",
        "embedding_content": "File: app.py\nSource:\ndef answer():\n    return 42\n",
    }

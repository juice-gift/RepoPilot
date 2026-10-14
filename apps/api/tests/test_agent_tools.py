import json
from dataclasses import asdict
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session

from repopilot.agent.models import Evidence, Observation
from repopilot.agent.tools import RunScope, ToolRegistry, bound_observation
from repopilot.embeddings.providers import DeterministicEmbeddingProvider
from repopilot.intelligence.navigation import SymbolView
from repopilot.intelligence.service import SnapshotNotFoundError
from repopilot.retrieval.retriever import RetrievalEvidence


@pytest.fixture
def registry(monkeypatch: pytest.MonkeyPatch) -> ToolRegistry:
    monkeypatch.setattr("repopilot.agent.tools.require_snapshot", MagicMock())
    return ToolRegistry(
        MagicMock(spec=Session),
        RunScope(1, 2),
        embedding_factory=DeterministicEmbeddingProvider,
    )


@pytest.mark.parametrize(
    "name,args",
    [
        ("shell", "{}"),
        ("read_file", "not json"),
        ("read_file", '{"path":"../secret.py"}'),
        ("read_file", '{"path":"C:/secret.py"}'),
        ("read_file", '{"path":"/etc/passwd"}'),
        ("read_file", '{"path":"a\\\\b.py"}'),
        ("read_file", '{"path":"a/./b.py"}'),
        ("read_file", '{"path":"a.py","repository_id":9}'),
        ("read_file", '{"path":"a.py","snapshot_id":9}'),
        ("read_file", '{"path":"a.py","start_line":3,"end_line":2}'),
        ("read_file", '{"path":"a.py","end_line":201}'),
        ("read_file", '{"path":"a.py","start_line":"1"}'),
        ("read_file", '{"path":"a.py","start_line":true}'),
        ("list_files", '{"limit":101}'),
        ("list_files", "[]"),
        ("search_code", '{"query":"  "}'),
        ("search_symbol", '{"query":"x","match":"fuzzy"}'),
        ("retrieve_context", '{"query":"x","top_k":11}'),
        ("retrieve_context", '{"query":"   "}'),
    ],
)
def test_rejects_unknown_invalid_and_scope_override(registry, name, args):
    result = registry.execute(name, args, evidence_prefix="E1")
    assert result.observation.status == "error"
    assert result.validated_arguments is None
    registry.session.scalar.assert_not_called()


def test_allowlist_and_typed_schema(registry):
    definitions = registry.definitions()
    assert [d["name"] for d in definitions] == [
        "list_files",
        "read_file",
        "search_code",
        "search_symbol",
        "retrieve_context",
    ]
    for definition in definitions:
        schema = definition["parameters"]
        assert schema["additionalProperties"] is False
        assert "repository_id" not in schema["properties"]
        assert "snapshot_id" not in schema["properties"]


def test_read_range_and_unknown_path(registry):
    registry.session.scalar.return_value = SimpleNamespace(
        path="a.py", language="python", content="one\ntwo\nthree\n"
    )
    result = registry.execute(
        "read_file", '{"path":"a.py","start_line":2,"end_line":3}', evidence_prefix="E1"
    )
    item = result.observation.items[0]
    assert (item.start_line, item.end_line, item.content) == (2, 3, "two\nthree")
    assert item.evidence_id == "E1_1"
    assert (
        registry.execute(
            "read_file", '{"path":"a.py","start_line":4}', evidence_prefix="E2"
        ).observation.error_code
        == "invalid_range"
    )
    registry.session.scalar.return_value = None
    assert (
        registry.execute(
            "read_file", '{"path":"missing.py"}', evidence_prefix="E3"
        ).observation.error_code
        == "file_not_found"
    )


def test_literal_search_order_and_bound(registry):
    registry.session.scalars.return_value = [
        SimpleNamespace(
            path="a.py",
            language="python",
            content="100%_literal\nother\n100%_literal\n",
        )
    ]
    result = registry.execute(
        "search_code", '{"query":"%_","limit":1}', evidence_prefix="E1"
    )
    assert result.observation.items[0].start_line == 1
    assert result.observation.omitted_items == 1
    statement = registry.session.scalars.call_args.args[0]
    assert statement.compile().params["content_1"] == "/%/_"


def test_v2_symbol_and_v1_retrieval_are_reused(registry, monkeypatch):
    symbol = SymbolView(
        id=4,
        snapshot_id=2,
        index_version="structural-v2",
        file_path="a.py",
        language="python",
        kind="function",
        name="run",
        qualified_name="run",
        parent_symbol_id=None,
        start_line=1,
        end_line=3,
    )
    search = MagicMock(return_value=[symbol])
    monkeypatch.setattr("repopilot.agent.tools.navigation.search_symbols", search)
    result = registry.execute("search_symbol", '{"query":"run"}', evidence_prefix="E1")
    assert result.observation.items[0].symbol_id == 4
    assert search.call_args.args[1:] == (1, 2)
    evidence = RetrievalEvidence(
        rank=1,
        chunk_id=9,
        file_path="a.py",
        language="python",
        chunk_type="function",
        symbol_name="run",
        qualified_name="run",
        parent_symbol=None,
        start_line=1,
        end_line=3,
        content_hash="abc",
        score=0.8,
        distance=0.2,
        content="def run(): pass",
    )
    retrieve = MagicMock(return_value=SimpleNamespace(evidence=(evidence,)))
    monkeypatch.setattr("repopilot.agent.tools.retrieve_evidence", retrieve)
    result = registry.execute(
        "retrieve_context", '{"query":"run"}', evidence_prefix="E2"
    )
    assert result.observation.items[0].score == 0.8
    assert retrieve.call_args.kwargs["snapshot_id"] == 2
    assert asdict(evidence)["content"] == result.observation.items[0].content


@pytest.mark.parametrize(
    "tool,args",
    [
        ("list_files", {}),
        ("read_file", {"path": "a.py"}),
        ("search_code", {"query": "x"}),
        ("search_symbol", {"query": "x"}),
        ("retrieve_context", {"query": "x"}),
    ],
)
def test_every_tool_checks_repository_and_snapshot(registry, monkeypatch, tool, args):
    require = MagicMock(side_effect=SnapshotNotFoundError("wrong scope"))
    monkeypatch.setattr("repopilot.agent.tools.require_snapshot", require)
    result = registry.execute(tool, json.dumps(args), evidence_prefix="E1")
    assert result.observation.error_code == "snapshot_not_found"
    require.assert_called_once_with(registry.session, 1, 2)


def test_full_json_size_bound_and_explicit_truncation():
    raw = Observation(
        items=[
            Evidence(
                file_path="a.py", start_line=1, end_line=1, content='"\\\n' * 20_000
            )
        ]
    )
    bounded = bound_observation(raw, 1_000)
    assert len(bounded.model_dump_json()) <= 1_000
    assert bounded.truncated
    assert bounded.items and bounded.items[0].truncated
    assert bounded.items[0].content
    assert len(raw.items[0].content) == 60_000
    assert json.loads(bounded.model_dump_json())["status"] == "ok"


def test_huge_arguments_and_safe_failure(registry):
    assert (
        registry.execute(
            "read_file", "x" * 4_001, evidence_prefix="E1"
        ).observation.error_code
        == "invalid_arguments"
    )
    registry.session.scalar.side_effect = RuntimeError("private credential")
    result = registry.execute("read_file", '{"path":"a.py"}', evidence_prefix="E1")
    assert result.observation.error_code == "tool_failure"
    assert "credential" not in result.model_dump_json()
    registry.session.rollback.assert_called_once()

from repopilot.rag.context import build_context
from repopilot.retrieval.retriever import RetrievalEvidence


def evidence(chunk_id: int, content: str, rank: int = 1) -> RetrievalEvidence:
    return RetrievalEvidence(
        rank=rank,
        chunk_id=chunk_id,
        file_path=f"file_{chunk_id}.py",
        language="python",
        chunk_type="function",
        symbol_name=f"symbol_{chunk_id}",
        qualified_name=f"symbol_{chunk_id}",
        parent_symbol=None,
        start_line=1,
        end_line=2,
        content_hash=str(chunk_id) * 64,
        score=0.9,
        distance=0.1,
        content=content,
    )


def test_context_builder_assigns_ids_and_deduplicates_chunk_ids() -> None:
    first = evidence(1, "def first():\n    return 1\n")
    duplicate = evidence(1, "def first():\n    return 1\n", rank=2)
    second = evidence(2, "def second():\n    return 2\n", rank=3)

    result = build_context(
        (first, duplicate, second), character_limit=2_000, max_evidence=8
    )

    assert [item.evidence_id for item in result.evidence] == ["E1", "E2"]
    assert [item.evidence.chunk_id for item in result.evidence] == [1, 2]
    assert result.omitted_evidence_count == 1
    assert "UNTRUSTED REPOSITORY EVIDENCE E1" in result.text
    assert result.character_count == len(result.text)


def test_context_builder_truncates_to_character_limit() -> None:
    result = build_context(
        (evidence(1, "x" * 2_000),), character_limit=1_000, max_evidence=1
    )

    assert len(result.text) <= 1_000
    assert result.evidence[0].truncated is True
    assert "[TRUNCATED BY CONTEXT CHARACTER LIMIT]" in result.text

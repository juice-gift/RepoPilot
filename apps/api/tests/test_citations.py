from repopilot.rag.citations import resolve_citations
from repopilot.rag.context import build_context
from repopilot.retrieval.retriever import RetrievalEvidence


def test_citations_resolve_only_backend_context_evidence() -> None:
    evidence = RetrievalEvidence(
        rank=1,
        chunk_id=42,
        file_path="service.py",
        language="python",
        chunk_type="function",
        symbol_name="run",
        qualified_name="Service.run",
        parent_symbol="Service",
        start_line=10,
        end_line=12,
        content_hash="a" * 64,
        score=0.88,
        distance=0.12,
        content="def run():\n    return True\n",
    )
    context = build_context((evidence,), character_limit=2_000, max_evidence=5)

    result = resolve_citations("Supported [E1], invented [E99], again [E1].", context)

    assert result.answer == (
        "Supported [E1], invented [invalid citation removed], again [E1]."
    )
    assert result.invalid_evidence_ids == ("E99",)
    assert len(result.citations) == 1
    citation = result.citations[0]
    assert citation.chunk_id == 42
    assert citation.file_path == "service.py"
    assert (citation.start_line, citation.end_line) == (10, 12)

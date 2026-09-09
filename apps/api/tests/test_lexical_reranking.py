from types import SimpleNamespace

from repopilot.indexing.vector_store import VectorSearchRow
from repopilot.retrieval.lexical import rerank_hybrid


def test_hybrid_reranking_uses_identifier_words_and_light_inflection() -> None:
    unrelated = SimpleNamespace(
        id=1,
        embedding_content="File Path: audit.js\nSymbol: appendAuditTimestamp",
    )
    relevant = SimpleNamespace(
        id=2,
        embedding_content=(
            "File Path: delivery.py\nSymbol: create_delivery_key\n"
            "Create a stable key that prevents duplicate event delivery."
        ),
    )
    rows = [
        VectorSearchRow(unrelated, "audit.js", 0.20),
        VectorSearchRow(relevant, "delivery.py", 0.24),
    ]

    reranked = rerank_hybrid(
        rows,
        question="What prevents the same event from being delivered twice?",
        limit=2,
    )

    assert reranked[0].vector_row.chunk.id == 2
    assert reranked[0].lexical_score > reranked[1].lexical_score


def test_hybrid_reranking_breaks_ties_deterministically() -> None:
    first = SimpleNamespace(id=2, embedding_content="nothing shared")
    second = SimpleNamespace(id=1, embedding_content="nothing shared")

    reranked = rerank_hybrid(
        [
            VectorSearchRow(first, "b.py", 0.5),
            VectorSearchRow(second, "a.py", 0.5),
        ],
        question="unmatched query",
        limit=2,
    )

    assert [item.vector_row.chunk.id for item in reranked] == [1, 2]

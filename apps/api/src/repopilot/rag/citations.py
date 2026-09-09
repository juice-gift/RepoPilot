import re
from dataclasses import dataclass

from repopilot.rag.context import ContextBuildResult


@dataclass(frozen=True)
class Citation:
    evidence_id: str
    chunk_id: int
    file_path: str
    symbol_name: str | None
    qualified_name: str | None
    start_line: int
    end_line: int
    score: float
    content: str


@dataclass(frozen=True)
class CitationResolution:
    answer: str
    citations: tuple[Citation, ...]
    invalid_evidence_ids: tuple[str, ...]


def resolve_citations(answer: str, context: ContextBuildResult) -> CitationResolution:
    evidence_by_id = {item.evidence_id: item.evidence for item in context.evidence}
    referenced_ids = list(dict.fromkeys(re.findall(r"\[(E\d+)\]", answer)))
    valid_ids = [item for item in referenced_ids if item in evidence_by_id]
    invalid_ids = [item for item in referenced_ids if item not in evidence_by_id]
    cleaned_answer = answer
    for evidence_id in invalid_ids:
        cleaned_answer = cleaned_answer.replace(
            f"[{evidence_id}]", "[invalid citation removed]"
        )
    citations = tuple(
        Citation(
            evidence_id=evidence_id,
            chunk_id=evidence_by_id[evidence_id].chunk_id,
            file_path=evidence_by_id[evidence_id].file_path,
            symbol_name=evidence_by_id[evidence_id].symbol_name,
            qualified_name=evidence_by_id[evidence_id].qualified_name,
            start_line=evidence_by_id[evidence_id].start_line,
            end_line=evidence_by_id[evidence_id].end_line,
            score=evidence_by_id[evidence_id].score,
            content=evidence_by_id[evidence_id].content,
        )
        for evidence_id in valid_ids
    )
    return CitationResolution(cleaned_answer, citations, tuple(invalid_ids))

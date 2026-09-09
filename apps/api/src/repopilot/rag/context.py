from dataclasses import dataclass

from repopilot.retrieval.retriever import RetrievalEvidence


@dataclass(frozen=True)
class ContextEvidence:
    evidence_id: str
    evidence: RetrievalEvidence
    formatted_content: str
    truncated: bool


@dataclass(frozen=True)
class ContextBuildResult:
    text: str
    evidence: tuple[ContextEvidence, ...]
    character_count: int
    omitted_evidence_count: int


def build_context(
    evidence: tuple[RetrievalEvidence, ...],
    *,
    character_limit: int,
    max_evidence: int,
) -> ContextBuildResult:
    selected: list[ContextEvidence] = []
    blocks: list[str] = []
    seen_chunk_ids: set[int] = set()
    candidates = [item for item in evidence if item.chunk_id not in seen_chunk_ids]
    deduplicated: list[RetrievalEvidence] = []
    for item in candidates:
        if item.chunk_id in seen_chunk_ids:
            continue
        seen_chunk_ids.add(item.chunk_id)
        deduplicated.append(item)

    for item in deduplicated[:max_evidence]:
        evidence_id = f"E{len(selected) + 1}"
        header = (
            f"--- BEGIN UNTRUSTED REPOSITORY EVIDENCE {evidence_id} ---\n"
            f"chunk_id: {item.chunk_id}\n"
            f"file: {item.file_path}\n"
            f"symbol: {item.qualified_name or item.symbol_name or '(none)'}\n"
            f"lines: {item.start_line}-{item.end_line}\n"
            f"score: {item.score}\n"
            "content:\n"
        )
        footer = f"\n--- END UNTRUSTED REPOSITORY EVIDENCE {evidence_id} ---"
        separator_size = 2 if blocks else 0
        available = character_limit - sum(len(block) for block in blocks) - separator_size
        if available <= len(header) + len(footer):
            break
        content_limit = available - len(header) - len(footer)
        truncated = len(item.content) > content_limit
        content = item.content[:content_limit]
        if truncated:
            marker = "\n[TRUNCATED BY CONTEXT CHARACTER LIMIT]"
            content = content[: max(0, content_limit - len(marker))] + marker
        block = f"{header}{content}{footer}"
        blocks.append(block)
        selected.append(ContextEvidence(evidence_id, item, block, truncated))

    text = "\n\n".join(blocks)
    return ContextBuildResult(
        text=text,
        evidence=tuple(selected),
        character_count=len(text),
        omitted_evidence_count=len(evidence) - len(selected),
    )

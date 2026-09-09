import { isRecord, requestJson } from "./client";

export interface Evidence {
  evidence_id?: string | null;
  included_in_context?: boolean;
  truncated?: boolean;
  rank: number;
  chunk_id: number;
  file_path: string;
  language: string;
  chunk_type: string;
  symbol_name: string | null;
  qualified_name: string | null;
  parent_symbol: string | null;
  start_line: number;
  end_line: number;
  content_hash: string;
  score: number;
  distance: number;
  content: string;
}

export interface RetrieveResponse {
  repository_id: number;
  snapshot_id: number;
  question: string;
  top_k: number;
  embedding_provider: string;
  embedding_model: string;
  retrieval_strategy: "vector" | "hybrid";
  duration_ms: number;
  evidence: Evidence[];
}

export interface Citation {
  evidence_id: string;
  chunk_id: number;
  file_path: string;
  symbol_name: string | null;
  qualified_name: string | null;
  start_line: number;
  end_line: number;
  score: number;
  content: string;
}

export interface AskResponse {
  status: "answered" | "insufficient_evidence";
  repository_id: number;
  snapshot_id: number;
  question: string;
  answer: string;
  embedding_provider: string;
  embedding_model: string;
  retrieval_strategy: "vector" | "hybrid";
  generation_provider: string;
  generation_model: string;
  retrieval_duration_ms: number;
  generation_duration_ms: number;
  context_character_count: number;
  context_character_limit: number;
  omitted_evidence_count: number;
  invalid_evidence_ids: string[];
  citations: Citation[];
  evidence: Evidence[];
}

function isEvidence(value: unknown): value is Evidence {
  return isRecord(value)
    && typeof value.rank === "number"
    && typeof value.chunk_id === "number"
    && typeof value.file_path === "string"
    && typeof value.language === "string"
    && typeof value.chunk_type === "string"
    && typeof value.start_line === "number"
    && typeof value.end_line === "number"
    && typeof value.score === "number"
    && typeof value.distance === "number"
    && typeof value.content === "string";
}

function isRetrieveResponse(value: unknown): value is RetrieveResponse {
  return isRecord(value)
    && typeof value.repository_id === "number"
    && typeof value.snapshot_id === "number"
    && typeof value.question === "string"
    && typeof value.top_k === "number"
    && typeof value.embedding_provider === "string"
    && typeof value.embedding_model === "string"
    && (value.retrieval_strategy === "vector" || value.retrieval_strategy === "hybrid")
    && typeof value.duration_ms === "number"
    && Array.isArray(value.evidence)
    && value.evidence.every(isEvidence);
}

function isCitation(value: unknown): value is Citation {
  return isRecord(value)
    && typeof value.evidence_id === "string"
    && typeof value.chunk_id === "number"
    && typeof value.file_path === "string"
    && typeof value.start_line === "number"
    && typeof value.end_line === "number"
    && typeof value.score === "number"
    && typeof value.content === "string";
}

function isAskResponse(value: unknown): value is AskResponse {
  return isRecord(value)
    && (value.status === "answered" || value.status === "insufficient_evidence")
    && typeof value.answer === "string"
    && typeof value.embedding_provider === "string"
    && typeof value.embedding_model === "string"
    && (value.retrieval_strategy === "vector" || value.retrieval_strategy === "hybrid")
    && typeof value.generation_provider === "string"
    && typeof value.generation_model === "string"
    && typeof value.retrieval_duration_ms === "number"
    && typeof value.generation_duration_ms === "number"
    && typeof value.context_character_count === "number"
    && Array.isArray(value.citations)
    && value.citations.every(isCitation)
    && Array.isArray(value.evidence)
    && value.evidence.every(isEvidence);
}

export async function retrieveEvidence(
  repositoryId: number,
  snapshotId: number,
  question: string,
  topK: number,
): Promise<RetrieveResponse> {
  return requestJson("/api/retrieve", isRetrieveResponse, {
    method: "POST",
    body: JSON.stringify({
      repository_id: repositoryId,
      snapshot_id: snapshotId,
      question,
      top_k: topK,
    }),
  });
}

export async function askQuestion(
  repositoryId: number,
  snapshotId: number,
  question: string,
  topK: number,
): Promise<AskResponse> {
  return requestJson("/api/ask", isAskResponse, {
    method: "POST",
    body: JSON.stringify({
      repository_id: repositoryId,
      snapshot_id: snapshotId,
      question,
      top_k: topK,
    }),
  });
}

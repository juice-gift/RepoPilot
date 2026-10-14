import { isRecord, requestJson } from "./client";

export interface AgentEvidence {
  evidence_id: string | null;
  file_path: string;
  language: string | null;
  symbol_name: string | null;
  qualified_name: string | null;
  symbol_id: number | null;
  start_line: number | null;
  end_line: number | null;
  content: string | null;
  rank: number | null;
  score: number | null;
  distance: number | null;
  truncated: boolean;
}

export interface Observation {
  status: "ok" | "error";
  items: AgentEvidence[];
  omitted_items: number;
  truncated: boolean;
  error_code: string | null;
  error_message: string | null;
}

export interface TraceStep {
  step: number;
  model_turn: number;
  call_id: string;
  tool_name: string;
  validated_arguments: Record<string, unknown> | null;
  observation: Observation;
  duration_ms: number;
}

const stopReasons = ["completed", "max_steps", "context_limit", "model_output_limit",
  "invalid_model_response", "provider_failure", "tool_failure"] as const;

export interface AgentResult {
  repository_id: number;
  snapshot_id: number;
  final_answer: string;
  trace: TraceStep[];
  sources: AgentEvidence[];
  total_steps: number;
  stop_reason: typeof stopReasons[number];
  diagnostics: {
    provider: string;
    model: string;
    model_calls: number;
    tool_failures: number;
    input_character_count: number;
    max_steps: number;
    observation_character_limit: number;
    context_character_limit: number;
    model_output_character_limit: number;
    duration_ms: number;
    invalid_evidence_ids: string[];
    failure: string | null;
  };
}

function nullableString(value: unknown): boolean {
  return value === null || typeof value === "string";
}

function nullableNumber(value: unknown): boolean {
  return value === null || typeof value === "number";
}

function isEvidence(value: unknown): value is AgentEvidence {
  return isRecord(value) && typeof value.file_path === "string"
    && ["evidence_id", "language", "symbol_name", "qualified_name", "content"].every((key) => nullableString(value[key]))
    && ["symbol_id", "start_line", "end_line", "rank", "score", "distance"].every((key) => nullableNumber(value[key]))
    && typeof value.truncated === "boolean";
}

function isObservation(value: unknown): value is Observation {
  return isRecord(value) && (value.status === "ok" || value.status === "error")
    && Array.isArray(value.items) && value.items.every(isEvidence)
    && typeof value.omitted_items === "number" && typeof value.truncated === "boolean"
    && nullableString(value.error_code) && nullableString(value.error_message);
}

function isTrace(value: unknown): value is TraceStep {
  return isRecord(value) && typeof value.step === "number" && typeof value.model_turn === "number"
    && typeof value.call_id === "string" && typeof value.tool_name === "string"
    && (value.validated_arguments === null || isRecord(value.validated_arguments))
    && isObservation(value.observation) && typeof value.duration_ms === "number";
}

export function isAgentResult(value: unknown): value is AgentResult {
  if (!isRecord(value) || !isRecord(value.diagnostics)) return false;
  const diagnostics = value.diagnostics;
  return typeof value.repository_id === "number" && typeof value.snapshot_id === "number"
    && typeof value.final_answer === "string" && typeof value.total_steps === "number"
    && stopReasons.some((reason) => value.stop_reason === reason)
    && Array.isArray(value.trace) && value.trace.every(isTrace)
    && Array.isArray(value.sources) && value.sources.every(isEvidence)
    && typeof diagnostics.provider === "string" && typeof diagnostics.model === "string"
    && ["model_calls", "tool_failures", "input_character_count", "max_steps",
      "observation_character_limit", "context_character_limit", "model_output_character_limit", "duration_ms"]
      .every((key) => typeof diagnostics[key] === "number")
    && nullableString(diagnostics.failure)
    && Array.isArray(diagnostics.invalid_evidence_ids)
    && diagnostics.invalid_evidence_ids.every((id) => typeof id === "string");
}

export function investigate(repositoryId: number, snapshotId: number, question: string): Promise<AgentResult> {
  return requestJson("/api/agent/investigate", isAgentResult, {
    method: "POST", body: JSON.stringify({ repository_id: repositoryId, snapshot_id: snapshotId, question }),
  });
}

interface StructureIndex {
  snapshot_id: number;
  index_version: string;
  symbol_count: number;
  import_count: number;
  reference_count: number;
  created: boolean;
}

export function prepareSymbols(repositoryId: number, snapshotId: number): Promise<StructureIndex> {
  return requestJson(`/api/repositories/${repositoryId}/snapshots/${snapshotId}/structure/index`,
    (value): value is StructureIndex => isRecord(value)
      && typeof value.snapshot_id === "number" && typeof value.index_version === "string"
      && typeof value.symbol_count === "number" && typeof value.import_count === "number"
      && typeof value.reference_count === "number" && typeof value.created === "boolean",
    { method: "POST" });
}

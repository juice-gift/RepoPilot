import { isRecord, requestJson } from "./client";

export type ResolutionProfile = "fee-days" | "dispatch-preconditions" | "ambiguous-cap";
interface Plan {
  expected_revision: number;
  decision: "repair" | "needs_owner_decision" | "insufficient_evidence";
  summary: string;
  steps: string[];
  files: string[];
}
interface TestResult {
  workspace_id: string;
  revision: number;
  profile: string;
  exit_code: number | null;
  stdout: string;
  stderr: string;
  elapsed_ms: number;
  timed_out: boolean;
  truncated: boolean;
  infrastructure_error: string | null;
  isolation_confirmed: boolean;
  cleanup_confirmed: boolean;
  expected_tests: number;
  observed_passed: number;
  passed: boolean;
}
interface ResolutionTrace {
  step: number;
  model_turn: number;
  call_id: string;
  tool_name: string;
  arguments: Record<string, unknown> | null;
  observation: { status: "ok" | "error"; payload: Record<string, unknown>; error_code: string | null; truncated: boolean };
  duration_ms: number;
}
interface PatchRecord {
  attempt: number;
  base_revision: number;
  revision: number;
  changed_paths: string[];
  before_hashes: Record<string, string>;
  after_hashes: Record<string, string>;
}
const repairStatuses = ["verified_repair", "incomplete_repair", "insufficient_evidence", "needs_owner_decision"] as const;
const stopReasons = ["completed", "max_steps", "context_limit", "model_output_limit", "invalid_model_response", "provider_failure", "tool_failure", "patch_limit", "test_limit", "wall_time_limit", "sandbox_failure"] as const;
export interface ResolutionResult {
  repository_id: number;
  snapshot_id: number;
  workspace_id: string;
  revision: number;
  profile: ResolutionProfile;
  execution_status: "completed" | "stopped";
  repair_status: typeof repairStatuses[number];
  final_answer: string;
  plans: Plan[];
  patch: string;
  changed_files: { path: string; original: string; modified: string }[];
  patch_history: PatchRecord[];
  test_results: TestResult[];
  trace: ResolutionTrace[];
  stop_reason: typeof stopReasons[number];
  diagnostics: {
    provider: string; model: string; model_calls: number; patch_attempts: number;
    test_executions: number; duration_ms: number; limits: Record<string, number>; failure: string | null;
  };
  workspace_cleaned: boolean;
}
const strings = (value: unknown): value is string[] => Array.isArray(value) && value.every((v) => typeof v === "string");
const nullableString = (value: unknown) => value === null || typeof value === "string";
const stringRecord = (value: unknown) => isRecord(value) && Object.values(value).every((v) => typeof v === "string");

export function isResolutionResult(value: unknown): value is ResolutionResult {
  if (!isRecord(value) || !isRecord(value.diagnostics)) return false;
  const d = value.diagnostics;
  return ["repository_id", "snapshot_id", "revision"].every((k) => typeof value[k] === "number")
    && typeof value.workspace_id === "string" && typeof value.final_answer === "string" && typeof value.patch === "string"
    && ["fee-days", "dispatch-preconditions", "ambiguous-cap"].some((v) => v === value.profile)
    && (value.execution_status === "completed" || value.execution_status === "stopped")
    && repairStatuses.some((v) => v === value.repair_status) && stopReasons.some((v) => v === value.stop_reason)
    && typeof value.workspace_cleaned === "boolean"
    && Array.isArray(value.plans) && value.plans.every((p) => isRecord(p) && typeof p.expected_revision === "number" && ["repair", "needs_owner_decision", "insufficient_evidence"].some((v) => v === p.decision) && typeof p.summary === "string" && strings(p.steps) && strings(p.files))
    && Array.isArray(value.changed_files) && value.changed_files.every((f) => isRecord(f) && ["path", "original", "modified"].every((k) => typeof f[k] === "string"))
    && Array.isArray(value.patch_history) && value.patch_history.every((p) => isRecord(p) && ["attempt", "base_revision", "revision"].every((k) => typeof p[k] === "number") && strings(p.changed_paths) && stringRecord(p.before_hashes) && stringRecord(p.after_hashes))
    && Array.isArray(value.test_results) && value.test_results.every((t) => isRecord(t)
      && ["workspace_id", "profile", "stdout", "stderr"].every((k) => typeof t[k] === "string")
      && ["revision", "elapsed_ms", "expected_tests", "observed_passed"].every((k) => typeof t[k] === "number")
      && (t.exit_code === null || typeof t.exit_code === "number") && nullableString(t.infrastructure_error)
      && ["timed_out", "truncated", "isolation_confirmed", "cleanup_confirmed", "passed"].every((k) => typeof t[k] === "boolean"))
    && Array.isArray(value.trace) && value.trace.every((t) => isRecord(t)
      && ["step", "model_turn", "duration_ms"].every((k) => typeof t[k] === "number")
      && typeof t.call_id === "string" && typeof t.tool_name === "string" && (t.arguments === null || isRecord(t.arguments))
      && isRecord(t.observation) && (t.observation.status === "ok" || t.observation.status === "error")
      && isRecord(t.observation.payload) && nullableString(t.observation.error_code) && typeof t.observation.truncated === "boolean")
    && typeof d.provider === "string" && typeof d.model === "string" && nullableString(d.failure)
    && ["model_calls", "patch_attempts", "test_executions", "duration_ms"].every((k) => typeof d[k] === "number")
    && isRecord(d.limits) && Object.values(d.limits).every((v) => typeof v === "number");
}

export function resolveIssue(repositoryId: number, snapshotId: number, issue: string, profile: ResolutionProfile): Promise<ResolutionResult> {
  return requestJson("/api/agent/resolve", isResolutionResult, {
    method: "POST", body: JSON.stringify({ repository_id: repositoryId, snapshot_id: snapshotId, issue, profile }),
  });
}

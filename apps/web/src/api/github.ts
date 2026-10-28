import { isRecord, requestJson } from "./client";
import { isResolutionResult, type ResolutionResult } from "./resolution";

export interface Binding { id: number; repository_full_name: string; issue_number: number; commit_sha: string; snapshot_id: number; profile: string }
export interface BoundRun { id: string; binding_id: number; state: string; result: ResolutionResult | null; result_hash: string | null; failure: string | null }
export interface Proposal {
  id: string; plan_hash: string; state: string; approved: boolean; last_error: string | null; outcome: Record<string, unknown>;
  plan: { proposal_id: string; run_id: string; result_hash: string; repository: string; issue_number: number; profile: string; base_sha: string; base_branch: string; head_branch: string; changed_paths: string[]; diff: string; commit_sha: string; tree_sha: string; test_passed: number; tested_revision: number; pr_title: string; pr_body: string; draft: true };
}
function binding(v: unknown): v is Binding { return isRecord(v) && typeof v.id === "number" && typeof v.repository_full_name === "string" && typeof v.commit_sha === "string" && typeof v.issue_number === "number" && typeof v.snapshot_id === "number" && typeof v.profile === "string"; }
function run(v: unknown): v is BoundRun { return isRecord(v) && typeof v.id === "string" && typeof v.binding_id === "number" && typeof v.state === "string" && (v.result === null || isResolutionResult(v.result)) && (v.result_hash === null || typeof v.result_hash === "string") && (v.failure === null || typeof v.failure === "string"); }
function proposal(v: unknown): v is Proposal {
  if (!isRecord(v) || !isRecord(v.plan)) return false;
  const p = v.plan;
  return typeof v.id === "string" && typeof v.plan_hash === "string" && typeof v.state === "string" && typeof v.approved === "boolean" && (v.last_error === null || typeof v.last_error === "string") && isRecord(v.outcome)
    && ["proposal_id", "run_id", "result_hash", "repository", "profile", "base_sha", "base_branch", "head_branch", "diff", "commit_sha", "tree_sha", "pr_title", "pr_body"].every(k => typeof p[k] === "string")
    && typeof p.issue_number === "number" && typeof p.test_passed === "number" && typeof p.tested_revision === "number" && p.draft === true
    && Array.isArray(p.changed_paths) && p.changed_paths.every(path => typeof path === "string");
}
export const listBindings = () => requestJson("/api/github/bindings", (v): v is Binding[] => Array.isArray(v) && v.every(binding));
export const listBoundRuns = () => requestJson("/api/github/runs", (v): v is BoundRun[] => Array.isArray(v) && v.every(run));
export const importGitHub = (repository: string, commit: string, issue_numbers: number[]) => requestJson("/api/github/import", (v): v is Binding[] => Array.isArray(v) && v.every(binding), { method: "POST", body: JSON.stringify({ repository, commit, issue_numbers }) });
export const resolveBinding = (binding_id: number) => requestJson("/api/github/runs", run, { method: "POST", body: JSON.stringify({ binding_id }) });
export const prepareProposal = (run_id: string) => requestJson("/api/github/proposals", proposal, { method: "POST", body: JSON.stringify({ run_id }) });
export const approveProposal = (p: Proposal) => requestJson(`/api/github/proposals/${p.id}/approve`, proposal, { method: "POST", body: JSON.stringify({ expected_hash: p.plan_hash, confirmation: `APPROVE ${p.id}:${p.plan_hash}` }) });
export const revokeProposal = (id: string) => requestJson(`/api/github/proposals/${id}/revoke`, proposal, { method: "POST" });
export const publishProposal = (id: string) => requestJson(`/api/github/proposals/${id}/publish`, proposal, { method: "POST" });

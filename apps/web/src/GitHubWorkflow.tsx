import { useEffect, useState } from "react";
import { ResolutionChanges, ResolutionSummary } from "./ResolutionResult";
import { approveProposal, importGitHub, importTrustedProfile, listTrustedProfiles, listBindings, listBoundRuns, prepareProposal, publishProposal, resolveBinding, revokeProposal, type Binding, type BoundRun, type Proposal, type TrustedProfile } from "./api/github";

export function GitHubWorkflow() {
  const [bindings, setBindings] = useState<Binding[]>([]);
  const [runs, setRuns] = useState<BoundRun[]>([]);
  const [selected, setSelected] = useState<BoundRun | null>(null);
  const [proposal, setProposal] = useState<Proposal | null>(null);
  const [repository, setRepository] = useState("");
  const [commit, setCommit] = useState("");
  const [issues, setIssues] = useState("1,2,3");
  const [confirm, setConfirm] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [profiles, setProfiles] = useState<TrustedProfile[]>([]);
  const [profile, setProfile] = useState("");
  async function refresh() { const [b, r, p] = await Promise.all([listBindings(), listBoundRuns(), listTrustedProfiles()]); setBindings(b); setRuns(r); setProfiles(p); }
  useEffect(() => { void refresh().catch(e => setError(String(e))); }, []);
  async function act(fn: () => Promise<void>) { setBusy(true); setError(""); try { await fn(); await refresh(); } catch (e) { setError(e instanceof Error ? e.message : "GitHub operation failed"); } finally { setBusy(false); } }
  function select(r: BoundRun) { setSelected(r); setProposal(null); setConfirm(false); }
  const prUrl = proposal?.outcome.pr_url;
  const safePr = typeof prUrl === "string" && /^https:\/\/github\.com\/[A-Za-z0-9-]+\/[A-Za-z0-9_.-]+\/pull\/\d+$/.test(prUrl) ? prUrl : null;
  return <section className="panel" style={{ margin: "1rem", padding: "1rem" }} aria-labelledby="github-title">
    <h2 id="github-title">GitHub controlled repair</h2>
    <p>Import an approved Issue at its fixed commit, inspect a saved repair, then review its exact publication plan. Repository content and model explanations are untrusted evidence.</p>
    <form onSubmit={e => { e.preventDefault(); void act(async () => { await importTrustedProfile(profile); }); }}>
      <label>Approved Python Issue<select value={profile} onChange={e => setProfile(e.target.value)}><option value="">Select an approved profile</option>{profiles.map(p => <option key={p.profile} value={p.profile}>{p.repository} #{p.issue_number} · {p.commit_sha.slice(0, 12)}</option>)}</select></label>
      <button disabled={busy || !profile}>Read and bind approved Issue</button>
      {!profiles.length && <p>No approved Python Issues are available in this server configuration.</p>}
    </form>
    <details><summary>Frozen regression fixture import</summary>
    <form onSubmit={e => { e.preventDefault(); void act(async () => { await importGitHub(repository, commit, issues.split(",").map(v => Number(v.trim()))); }); }}>
      <label>Authorized owner/repository<input value={repository} onChange={e => setRepository(e.target.value)} placeholder="owner/repository" required /></label>
      <label>Full baseline commit SHA<input value={commit} onChange={e => setCommit(e.target.value)} pattern="[a-f0-9]{40}" required /></label>
      <label>Issue numbers: fee-days, dispatch-preconditions, ambiguous-cap<input value={issues} onChange={e => setIssues(e.target.value)} required /></label>
      <button disabled={busy}>Read and verify fixture</button>
    </form>
    </details>
    {error && <p role="alert">{error}</p>}
    <h3>Saved Issue versions</h3>
    {bindings.map(b => <p key={b.id}>{b.repository_full_name} #{b.issue_number} · {b.profile} · <code>{b.commit_sha}</code> · Snapshot {b.snapshot_id} <button disabled={busy} onClick={() => void act(async () => { const r = await resolveBinding(b.id); select(r); })}>Run controlled repair</button></p>)}
    <label>Saved repair<select value={selected?.id ?? ""} onChange={e => { const r = runs.find(v => v.id === e.target.value); if (r) select(r); }}><option value="">Select a saved run</option>{runs.map(r => <option key={r.id} value={r.id}>{r.id.slice(0, 8)} · {r.state} · {r.result?.repair_status ?? r.failure}</option>)}</select></label>
    {selected?.result && <><ResolutionSummary result={selected.result} /><ResolutionChanges result={selected.result} /><button disabled={busy || selected.result.repair_status !== "verified_repair"} onClick={() => void act(async () => { setConfirm(false); setProposal(await prepareProposal(selected.id)); })}>Prepare publication for review</button></>}
    {proposal && <div>
      <h3>Exact publication proposal · {proposal.state}</h3>
      <p>{proposal.plan.repository} #{proposal.plan.issue_number} · draft PR</p>
      <p>Base <code>{proposal.plan.base_sha}</code> → <code>{proposal.plan.head_branch}</code></p>
      <p>Commit <code>{proposal.plan.commit_sha}</code> · {proposal.plan.test_passed} independent tests at revision {proposal.plan.tested_revision}</p>
      <p>Approval digest <code>{proposal.plan_hash}</code></p><pre>{proposal.plan.diff}</pre>
      {proposal.plan.baseline_entries && <p>Historical public-source repair. Publication requires a separately authorized private repository owned by the operator and an exact current main baseline. This proposal grants no remote write authority; a public upstream or stale baseline will be refused.</p>}
      <details><summary>PR description and result identity</summary><pre>{proposal.plan.pr_title}{"\n"}{proposal.plan.pr_body}{"\nResult hash: "}{proposal.plan.result_hash}</pre></details>
      <p>Creates one commit, a new dedicated branch and a draft PR. The default branch is not changed. No merge is authorized. A changed baseline or repair invalidates approval.</p>
      <label><input type="checkbox" checked={confirm} onChange={e => setConfirm(e.target.checked)} />I reviewed this repository, baseline, diff, tests, commit and PR and approve this exact proposal.</label>
      <button disabled={busy || !confirm || proposal.state !== "awaiting_approval"} onClick={() => void act(async () => { setProposal(await approveProposal(proposal)); setConfirm(false); })}>Approve exact proposal</button>
      <button disabled={busy || !proposal.approved || !["approved", "publishing", "retry_needed", "published"].includes(proposal.state)} onClick={() => void act(async () => setProposal(await publishProposal(proposal.id)))}>Publish or reconcile approved proposal</button>
      <button disabled={busy || !["awaiting_approval", "approved"].includes(proposal.state)} onClick={() => void act(async () => { setProposal(await revokeProposal(proposal.id)); setConfirm(false); })}>Revoke approval</button>
      {proposal.last_error && <p role="alert">{proposal.last_error}. Inspect the saved outcome before retrying.</p>}
      {safePr && <a href={safePr} target="_blank" rel="noreferrer">Open verified draft PR</a>}
    </div>}
  </section>;
}

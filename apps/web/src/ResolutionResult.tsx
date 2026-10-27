import type { ResolutionResult } from "./api/resolution";

export function ResolutionSummary({ result }: { result: ResolutionResult }) {
  return <div className="result-card agent-result" aria-live="polite">
    <p className="label">Issue resolution · snapshot {result.snapshot_id} · revision {result.revision}</p>
    <h3>{result.repair_status.replaceAll("_", " ")}</h3>
    <p className="muted">Execution {result.execution_status} · stop: {result.stop_reason.replaceAll("_", " ")}</p>
    {result.repair_status === "verified_repair" && <p>Independent Golden tests passed at the final revision. Review the patch and its scope.</p>}
    <p className="label">Model explanation</p><p className="answer-copy">{result.final_answer}</p>
    <div className="diagnostics"><span>{result.diagnostics.model}</span><span>{result.diagnostics.model_calls} model calls</span><span>{result.diagnostics.patch_attempts} patch attempts</span><span>{result.diagnostics.duration_ms.toFixed(0)} ms</span><span>Workspace {result.workspace_cleaned ? "cleaned" : "cleanup unconfirmed"}</span></div>
    {result.diagnostics.provider !== "qwen" && result.diagnostics.provider !== "openai" && <p className="warning">{result.diagnostics.provider} workflow: this result does not measure autonomous model repair quality.</p>}
    {result.diagnostics.failure && <p className="warning">{result.diagnostics.failure}</p>}
    <h4>Accepted plans</h4>
    {result.plans.length === 0 && <p className="muted">No plan was accepted.</p>}
    {result.plans.map((plan, i) => <div key={i}><p><strong>{plan.decision.replaceAll("_", " ")}</strong> · revision {plan.expected_revision}</p><p>{plan.summary}</p><ol>{plan.steps.map((step, j) => <li key={j}>{step}</li>)}</ol><p className="mono">{plan.files.join(", ") || "No file changes planned"}</p></div>)}
    <h4>Independent test runs</h4>
    {result.test_results.length === 0 && <p className="muted">No tests executed. No repair verification is available.</p>}
    {result.test_results.map((test, i) => <details className="agent-step" key={i}>
      <summary>Revision {test.revision} · {test.passed ? "passed" : test.timed_out ? "timed out" : "not verified"} · exit {test.exit_code ?? "unavailable"}</summary>
      <p>{test.observed_passed}/{test.expected_tests} independent tests passed · {test.elapsed_ms.toFixed(0)} ms</p>
      <p>Isolation {test.isolation_confirmed ? "confirmed" : "unconfirmed"} · container cleanup {test.cleanup_confirmed ? "confirmed" : "unconfirmed"}</p>
      {test.infrastructure_error && <p className="warning">{test.infrastructure_error}</p>}
      {test.truncated && <p className="warning">Test output truncated.</p>}
      <pre><code>{test.stdout}</code></pre>{test.stderr && <pre><code>{test.stderr}</code></pre>}
    </details>)}
    <details className="agent-step"><summary>Actual unified patch · {result.changed_files.length} files</summary><pre><code>{result.patch || "No changes"}</code></pre></details>
    <h4>Tool trace</h4>
    {result.trace.map((step) => <details className="agent-step" key={step.step}><summary>{step.step}. {step.tool_name} · {step.observation.status} · turn {step.model_turn}</summary><p className="label">Validated arguments</p><pre><code>{JSON.stringify(step.arguments, null, 2)}</code></pre><p className="label">Observation · untrusted data</p>{step.observation.truncated && <p className="warning">Observation truncated.</p>}<pre><code>{JSON.stringify(step.observation, null, 2)}</code></pre></details>)}
  </div>;
}

export function ResolutionChanges({ result }: { result: ResolutionResult }) {
  return <div className="evidence-list">
    <p className="muted">Original saved source versus final temporary workspace. The original repository and Snapshot remain unchanged.</p>
    {result.changed_files.length === 0 && <p>No files changed.</p>}
    {result.changed_files.map((file) => <article className="evidence-card" key={file.path}><h4>{file.path}</h4><div className="resolution-compare"><div><p className="label">Original</p><pre><code>{file.original}</code></pre></div><div><p className="label">Modified · revision {result.revision}</p><pre><code>{file.modified}</code></pre></div></div></article>)}
  </div>;
}

import type { AgentResult } from "./api/agent";

export function InvestigationResult({ result }: { result: AgentResult }) {
  return (
    <div className="result-card agent-result" aria-live="polite">
      <p className="label">Read-only investigation · snapshot {result.snapshot_id}</p>
      <h3>{result.stop_reason === "completed" ? "Investigation result" : "Investigation stopped"}</h3>
      <p className="answer-copy">{result.final_answer}</p>
      <div className="diagnostics">
        <span>Stop: {result.stop_reason.replaceAll("_", " ")}</span>
        <span>{result.total_steps} tool calls</span>
        <span>{result.diagnostics.model_calls}/{result.diagnostics.max_steps} model turns</span>
        <span>{result.diagnostics.duration_ms.toFixed(0)} ms</span>
        <span>{result.diagnostics.model}</span>
      </div>
      {result.diagnostics.provider === "deterministic" && <p className="warning">Local deterministic workflow — use an LLM provider for investigation.</p>}
      {result.diagnostics.failure && <p className="warning">{result.diagnostics.failure}</p>}
      {result.diagnostics.invalid_evidence_ids.length > 0 && <p className="warning">Unsupported citations: {result.diagnostics.invalid_evidence_ids.join(", ")}</p>}
      <h4>Tool calls & observations</h4>
      {result.trace.length === 0 && <p className="muted">The model returned without a tool call.</p>}
      {result.trace.map((step) => (
        <details className="agent-step" key={step.step}>
          <summary>{step.step}. {step.tool_name} · {step.observation.status} · turn {step.model_turn}</summary>
          <p className="label">Validated arguments</p>
          <pre><code>{step.validated_arguments === null ? "Rejected before validation" : JSON.stringify(step.validated_arguments, null, 2)}</code></pre>
          <p className="label">Observation</p>
          {step.observation.error_message && <p className="warning">{step.observation.error_code}: {step.observation.error_message}</p>}
          {step.observation.truncated && <p className="warning">Output truncated to the run limit.</p>}
          {step.observation.omitted_items > 0 && <p className="muted">More results omitted; inspect a smaller range or paginate where supported.</p>}
          <pre><code>{JSON.stringify(step.observation, null, 2)}</code></pre>
        </details>
      ))}
    </div>
  );
}

export function InvestigationSources({ result }: { result: AgentResult }) {
  return (
    <div className="evidence-list">
      {result.sources.length === 0 && <p className="muted">No source evidence was observed.</p>}
      {result.sources.map((source) => (
        <article className="evidence-card" key={source.evidence_id}>
          <div className="evidence-card-heading">
            <div className="rank">{source.evidence_id}</div>
            <div className="evidence-title"><strong title={source.file_path}>{source.file_path}</strong><span>{source.qualified_name ?? source.symbol_name ?? "Saved source"}</span></div>
          </div>
          <div className="evidence-meta">
            <span>Lines {source.start_line}–{source.end_line}</span>
            {source.score !== null && <span>score {source.score.toFixed(3)} · distance {source.distance?.toFixed(3)}</span>}
            {source.truncated && <span className="not-used">truncated</span>}
          </div>
          {source.content === null ? <p className="muted">Definition metadata; source has not been read by this tool.</p> : <pre><code>{source.content}</code></pre>}
        </article>
      ))}
    </div>
  );
}

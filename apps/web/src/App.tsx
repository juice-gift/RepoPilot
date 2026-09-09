import { useEffect, useMemo, useState } from "react";

import { getDatabaseHealth, getHealth } from "./api/health";
import {
  indexSnapshot,
  ingestRepository,
  listRepositories,
  listSnapshots,
  type IndexResponse,
  type IngestResponse,
  type Repository,
  type Snapshot,
} from "./api/repositories";
import {
  askQuestion,
  retrieveEvidence,
  type AskResponse,
  type Evidence,
  type RetrieveResponse,
} from "./api/rag";
import "./App.css";

type ConnectionStatus = "checking" | "connected" | "unavailable";
type Operation = "ingest" | "retrieve" | "ask" | null;

const statusMessages: Record<ConnectionStatus, string> = {
  checking: "Checking",
  connected: "Connected",
  unavailable: "Unavailable",
};

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "An unexpected error occurred";
}

function formatDate(value: string): string {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function App() {
  const [backendStatus, setBackendStatus] = useState<ConnectionStatus>("checking");
  const [databaseStatus, setDatabaseStatus] = useState<ConnectionStatus>("checking");
  const [repositories, setRepositories] = useState<Repository[]>([]);
  const [selectedRepositoryId, setSelectedRepositoryId] = useState<number | null>(null);
  const [snapshots, setSnapshots] = useState<Snapshot[]>([]);
  const [selectedSnapshotId, setSelectedSnapshotId] = useState<number | null>(null);
  const [repositoryPath, setRepositoryPath] = useState(".");
  const [repositoryName, setRepositoryName] = useState("");
  const [question, setQuestion] = useState("");
  const [topK, setTopK] = useState(5);
  const [operation, setOperation] = useState<Operation>(null);
  const [error, setError] = useState<string | null>(null);
  const [ingestion, setIngestion] = useState<IngestResponse | null>(null);
  const [indexing, setIndexing] = useState<IndexResponse | null>(null);
  const [retrieval, setRetrieval] = useState<RetrieveResponse | null>(null);
  const [answer, setAnswer] = useState<AskResponse | null>(null);
  const [focusedChunkId, setFocusedChunkId] = useState<number | null>(null);

  const selectedRepository = useMemo(
    () => repositories.find((item) => item.id === selectedRepositoryId) ?? null,
    [repositories, selectedRepositoryId],
  );
  const selectedSnapshot = useMemo(
    () => snapshots.find((item) => item.id === selectedSnapshotId) ?? null,
    [snapshots, selectedSnapshotId],
  );
  const visibleEvidence: Evidence[] = answer?.evidence ?? retrieval?.evidence ?? [];

  useEffect(() => {
    const controller = new AbortController();
    async function initialize(): Promise<void> {
      const [backend, database, repositoryResult] = await Promise.allSettled([
        getHealth(controller.signal),
        getDatabaseHealth(controller.signal),
        listRepositories(controller.signal),
      ]);
      if (controller.signal.aborted) return;
      setBackendStatus(backend.status === "fulfilled" ? "connected" : "unavailable");
      setDatabaseStatus(database.status === "fulfilled" ? "connected" : "unavailable");
      if (repositoryResult.status === "fulfilled") {
        setRepositories(repositoryResult.value);
        if (repositoryResult.value[0]) {
          setSelectedRepositoryId(repositoryResult.value[0].id);
        }
      }
    }
    void initialize();
    return () => controller.abort();
  }, []);

  useEffect(() => {
    if (selectedRepositoryId === null) {
      setSnapshots([]);
      setSelectedSnapshotId(null);
      return;
    }
    const controller = new AbortController();
    listSnapshots(selectedRepositoryId, controller.signal)
      .then((items) => {
        setSnapshots(items);
        setSelectedSnapshotId((current) =>
          items.some((item) => item.id === current) ? current : items[0]?.id ?? null,
        );
      })
      .catch((loadError: unknown) => {
        if (!(loadError instanceof DOMException && loadError.name === "AbortError")) {
          setError(errorMessage(loadError));
        }
      });
    return () => controller.abort();
  }, [selectedRepositoryId]);

  function resetQueryResults(): void {
    setRetrieval(null);
    setAnswer(null);
    setFocusedChunkId(null);
  }

  async function handleIngest(): Promise<void> {
    setOperation("ingest");
    setError(null);
    setIngestion(null);
    setIndexing(null);
    resetQueryResults();
    try {
      const ingestResult = await ingestRepository(repositoryPath, repositoryName.trim() || undefined);
      setIngestion(ingestResult);
      const indexResult = await indexSnapshot(
        ingestResult.repository.id,
        ingestResult.snapshot.id,
      );
      setIndexing(indexResult);
      const refreshedRepositories = await listRepositories();
      setRepositories(refreshedRepositories);
      setSelectedRepositoryId(ingestResult.repository.id);
      const refreshedSnapshots = await listSnapshots(ingestResult.repository.id);
      setSnapshots(refreshedSnapshots);
      setSelectedSnapshotId(ingestResult.snapshot.id);
    } catch (ingestError: unknown) {
      setError(errorMessage(ingestError));
    } finally {
      setOperation(null);
    }
  }

  async function handleRetrieve(): Promise<void> {
    if (selectedRepositoryId === null || selectedSnapshotId === null) return;
    setOperation("retrieve");
    setError(null);
    setAnswer(null);
    setFocusedChunkId(null);
    try {
      setRetrieval(
        await retrieveEvidence(selectedRepositoryId, selectedSnapshotId, question, topK),
      );
    } catch (retrieveError: unknown) {
      setRetrieval(null);
      setError(errorMessage(retrieveError));
    } finally {
      setOperation(null);
    }
  }

  async function handleAsk(): Promise<void> {
    if (selectedRepositoryId === null || selectedSnapshotId === null) return;
    setOperation("ask");
    setError(null);
    setRetrieval(null);
    setFocusedChunkId(null);
    try {
      setAnswer(await askQuestion(selectedRepositoryId, selectedSnapshotId, question, topK));
    } catch (askError: unknown) {
      setAnswer(null);
      setError(errorMessage(askError));
    } finally {
      setOperation(null);
    }
  }

  function focusEvidence(chunkId: number): void {
    setFocusedChunkId(chunkId);
    requestAnimationFrame(() => {
      document.getElementById("evidence-" + chunkId)?.scrollIntoView({
        behavior: "smooth",
        block: "center",
      });
    });
  }

  const canQuery = selectedRepositoryId !== null
    && selectedSnapshotId !== null
    && question.trim().length > 0
    && operation === null;

  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Codebase RAG · V1</p>
          <h1>RepoPilot</h1>
        </div>
        <div className="connections" role="status" aria-label="Service connections">
          <span className={"status status--" + backendStatus}>
            <i /> API {statusMessages[backendStatus]}
          </span>
          <span className={"status status--" + databaseStatus}>
            <i /> Database {statusMessages[databaseStatus]}
          </span>
        </div>
      </header>

      <main className="workspace">
        <aside className="panel repository-panel">
          <div className="panel-heading">
            <p className="step">01</p>
            <div><h2>Repository</h2><p>Snapshot and index local source</p></div>
          </div>
          <form onSubmit={(event) => { event.preventDefault(); void handleIngest(); }}>
            <label>
              Allowed local path
              <input value={repositoryPath} onChange={(event) => setRepositoryPath(event.target.value)} placeholder=". or project/subfolder" required />
            </label>
            <label>
              Display name <span>optional</span>
              <input value={repositoryName} onChange={(event) => setRepositoryName(event.target.value)} placeholder="RepoPilot" />
            </label>
            <button className="primary-button" disabled={operation !== null} type="submit">
              {operation === "ingest" ? "Scanning and indexing…" : "Ingest & index"}
            </button>
          </form>

          <div className="divider" />
          <label>
            Repository
            <select value={selectedRepositoryId ?? ""} onChange={(event) => { setSelectedRepositoryId(Number(event.target.value)); resetQueryResults(); }}>
              {repositories.length === 0 && <option value="">No repositories yet</option>}
              {repositories.map((repository) => <option key={repository.id} value={repository.id}>{repository.name}</option>)}
            </select>
          </label>
          <label>
            Snapshot
            <select value={selectedSnapshotId ?? ""} onChange={(event) => { setSelectedSnapshotId(Number(event.target.value)); resetQueryResults(); }}>
              {snapshots.length === 0 && <option value="">No snapshots yet</option>}
              {snapshots.map((snapshot) => (
                <option key={snapshot.id} value={snapshot.id}>
                  {snapshot.content_hash.slice(0, 10)} · {formatDate(snapshot.created_at)}
                </option>
              ))}
            </select>
          </label>

          {selectedRepository && (
            <div className="snapshot-card">
              <p className="mono path" title={selectedRepository.local_path}>{selectedRepository.local_path}</p>
              {selectedSnapshot ? (
                <dl>
                  <div><dt>Files</dt><dd>{selectedSnapshot.accepted_file_count}</dd></div>
                  <div><dt>Chunks</dt><dd>{selectedSnapshot.chunk_count}</dd></div>
                  <div><dt>Indexed</dt><dd>{selectedSnapshot.indexed_chunk_count}</dd></div>
                  <div><dt>Model</dt><dd>{selectedSnapshot.embedding_model ?? "Not indexed"}</dd></div>
                </dl>
              ) : <p className="muted">Choose or create a snapshot.</p>}
            </div>
          )}

          {(ingestion || indexing) && (
            <div className="run-summary">
              <p className="label">Latest index run</p>
              {ingestion && <p>{ingestion.snapshot_created ? "Created" : "Reused"} snapshot · {ingestion.snapshot.accepted_file_count} files · {ingestion.snapshot.skipped_file_count} skipped</p>}
              {indexing && <p>{indexing.index_reused ? "Reused" : "Embedded"} {indexing.embedded_chunk_count} chunks in {indexing.duration_ms.toFixed(1)} ms</p>}
            </div>
          )}
        </aside>

        <section className="panel question-panel">
          <div className="panel-heading">
            <p className="step">02</p>
            <div><h2>Question</h2><p>Inspect retrieval before trusting generation</p></div>
          </div>
          <label className="question-label">
            Ask about the selected snapshot
            <textarea value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="Where is database connectivity configured, and how does it fail?" rows={5} />
          </label>
          <div className="query-controls">
            <label>
              Top K
              <input
                className="top-k"
                type="number"
                min={1}
                max={20}
                value={topK}
                onChange={(event) => {
                  const value = Number(event.target.value);
                  setTopK(Number.isFinite(value) ? Math.min(20, Math.max(1, value)) : 1);
                }}
              />
            </label>
            <button className="secondary-button" disabled={!canQuery} onClick={() => void handleRetrieve()}>
              {operation === "retrieve" ? "Retrieving…" : "Retrieve evidence"}
            </button>
            <button className="primary-button" disabled={!canQuery} onClick={() => void handleAsk()}>
              {operation === "ask" ? "Generating…" : "Ask with evidence"}
            </button>
          </div>

          {error && <div className="error-banner" role="alert"><strong>Request failed</strong><span>{error}</span></div>}
          {!answer && !retrieval && !error && (
            <div className="empty-state">
              <div className="empty-mark">RP</div>
              <h3>Evidence stays visible</h3>
              <p>Run retrieval alone to debug ranking, or generate an answer with backend-resolved citations.</p>
            </div>
          )}
          {retrieval && (
            <div className="result-card retrieval-result">
              <p className="label">Retrieval only</p>
              <h3>{retrieval.evidence.length} ranked source chunks</h3>
              <p>No generation model was called. Use the evidence panel to judge relevance directly.</p>
              <div className="diagnostics">
                <span>{retrieval.embedding_model}</span><span>{retrieval.duration_ms.toFixed(1)} ms</span><span>Top {retrieval.top_k}</span>
              </div>
            </div>
          )}
          {answer && (
            <div className="result-card answer-card">
              <div className="answer-heading">
                <div><p className="label">Grounded answer</p><h3>{answer.status === "answered" ? "Answer" : "Insufficient evidence"}</h3></div>
                <span className={"answer-status answer-status--" + answer.status}>{answer.status.replace("_", " ")}</span>
              </div>
              <p className="answer-copy">{answer.answer}</p>
              {answer.citations.length > 0 && (
                <div className="citation-row" aria-label="Answer citations">
                  {answer.citations.map((citation) => (
                    <button key={citation.evidence_id} onClick={() => focusEvidence(citation.chunk_id)}>
                      {citation.evidence_id} · {citation.file_path}:{citation.start_line}-{citation.end_line}
                    </button>
                  ))}
                </div>
              )}
              <div className="diagnostics">
                <span>Retrieve {answer.retrieval_duration_ms.toFixed(1)} ms</span>
                <span>Generate {answer.generation_duration_ms.toFixed(1)} ms</span>
                <span>{answer.context_character_count}/{answer.context_character_limit} chars</span>
                <span>{answer.generation_model}</span>
              </div>
              {answer.invalid_evidence_ids.length > 0 && <p className="warning">Removed invalid model citations: {answer.invalid_evidence_ids.join(", ")}</p>}
            </div>
          )}
        </section>

        <aside className="panel evidence-panel">
          <div className="panel-heading evidence-heading">
            <p className="step">03</p>
            <div><h2>Evidence</h2><p>Why these chunks were selected</p></div>
            <span className="count-badge">{visibleEvidence.length}</span>
          </div>
          <div className="evidence-list">
            {visibleEvidence.length === 0 && (
              <div className="evidence-empty"><p>No evidence yet.</p><span>Ranked chunks, scores, symbols, line ranges, and source content will appear here.</span></div>
            )}
            {visibleEvidence.map((item) => (
              <article id={"evidence-" + item.chunk_id} key={item.chunk_id} className={"evidence-card " + (focusedChunkId === item.chunk_id ? "evidence-card--focused" : "")}>
                <div className="evidence-card-heading">
                  <div className="rank">{item.evidence_id ?? "#" + item.rank}</div>
                  <div className="evidence-title"><strong>{item.file_path}</strong><span>{item.qualified_name ?? item.symbol_name ?? item.chunk_type}</span></div>
                  <div className="score"><strong>{item.score.toFixed(3)}</strong><span>score</span></div>
                </div>
                <div className="evidence-meta">
                  <span>Lines {item.start_line}–{item.end_line}</span><span>{item.language}</span><span>{item.chunk_type}</span><span>distance {item.distance.toFixed(3)}</span>
                  {item.included_in_context === false && <span className="not-used">not in context</span>}
                  {item.truncated && <span className="not-used">truncated</span>}
                </div>
                <pre><code>{item.content}</code></pre>
              </article>
            ))}
          </div>
        </aside>
      </main>
    </div>
  );
}

export default App;

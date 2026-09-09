import { isRecord, requestJson } from "./client";

export interface Repository {
  id: number;
  name: string;
  local_path: string;
  created_at: string;
}

export interface Snapshot {
  id: number;
  repository_id: number;
  content_hash: string;
  source_revision: string | null;
  accepted_file_count: number;
  skipped_file_count: number;
  total_bytes: number;
  chunk_count: number;
  chunking_version: string | null;
  embedding_provider: string | null;
  embedding_model: string | null;
  embedding_dimensions: number | null;
  indexed_chunk_count: number;
  indexed_at: string | null;
  created_at: string;
}

export interface IngestResponse {
  repository: Repository;
  snapshot: Snapshot;
  snapshot_created: boolean;
  languages: Record<string, number>;
  skipped_reason_counts: Record<string, number>;
  skipped_files: Array<{ path: string; reason: string }>;
  excluded_directories: string[];
}

export interface IndexResponse {
  repository_id: number;
  snapshot_id: number;
  chunk_count: number;
  embedded_chunk_count: number;
  embedding_provider: string;
  embedding_model: string;
  embedding_dimensions: number;
  index_reused: boolean;
  duration_ms: number;
}

function isRepository(value: unknown): value is Repository {
  return isRecord(value)
    && typeof value.id === "number"
    && typeof value.name === "string"
    && typeof value.local_path === "string"
    && typeof value.created_at === "string";
}

function isSnapshot(value: unknown): value is Snapshot {
  return isRecord(value)
    && typeof value.id === "number"
    && typeof value.repository_id === "number"
    && typeof value.content_hash === "string"
    && typeof value.accepted_file_count === "number"
    && typeof value.skipped_file_count === "number"
    && typeof value.total_bytes === "number"
    && typeof value.chunk_count === "number"
    && typeof value.indexed_chunk_count === "number"
    && typeof value.created_at === "string";
}

function isIngestResponse(value: unknown): value is IngestResponse {
  return isRecord(value)
    && isRepository(value.repository)
    && isSnapshot(value.snapshot)
    && typeof value.snapshot_created === "boolean"
    && isRecord(value.languages)
    && isRecord(value.skipped_reason_counts)
    && Array.isArray(value.skipped_files)
    && Array.isArray(value.excluded_directories);
}

function isIndexResponse(value: unknown): value is IndexResponse {
  return isRecord(value)
    && typeof value.repository_id === "number"
    && typeof value.snapshot_id === "number"
    && typeof value.chunk_count === "number"
    && typeof value.embedded_chunk_count === "number"
    && typeof value.embedding_provider === "string"
    && typeof value.embedding_model === "string"
    && typeof value.embedding_dimensions === "number"
    && typeof value.index_reused === "boolean"
    && typeof value.duration_ms === "number";
}

export async function listRepositories(signal?: AbortSignal): Promise<Repository[]> {
  return requestJson(
    "/api/repositories",
    (value): value is Repository[] => Array.isArray(value) && value.every(isRepository),
    { signal },
  );
}

export async function listSnapshots(
  repositoryId: number,
  signal?: AbortSignal,
): Promise<Snapshot[]> {
  return requestJson(
    `/api/repositories/${repositoryId}/snapshots`,
    (value): value is Snapshot[] => Array.isArray(value) && value.every(isSnapshot),
    { signal },
  );
}

export async function ingestRepository(
  path: string,
  name?: string,
): Promise<IngestResponse> {
  return requestJson("/api/repositories/ingest", isIngestResponse, {
    method: "POST",
    body: JSON.stringify({ path, ...(name ? { name } : {}) }),
  });
}

export async function indexSnapshot(
  repositoryId: number,
  snapshotId: number,
): Promise<IndexResponse> {
  return requestJson(
    `/api/repositories/${repositoryId}/snapshots/${snapshotId}/index`,
    isIndexResponse,
    { method: "POST" },
  );
}

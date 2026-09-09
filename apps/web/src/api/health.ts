import { apiBaseUrl } from "./client";

export interface HealthResponse {
  status: "ok";
  service: "repopilot-api";
}

export interface DatabaseHealthResponse {
  status: "ok";
  database: "postgresql";
}

function isHealthResponse(value: unknown): value is HealthResponse {
  if (typeof value !== "object" || value === null) {
    return false;
  }

  const response = value as Record<string, unknown>;
  return response.status === "ok" && response.service === "repopilot-api";
}

export async function getHealth(signal?: AbortSignal): Promise<HealthResponse> {
  const response = await fetch(`${apiBaseUrl}/api/health`, { signal });

  if (!response.ok) {
    throw new Error(`Health request failed with status ${response.status}`);
  }

  const data: unknown = await response.json();
  if (!isHealthResponse(data)) {
    throw new Error("Health response did not match the expected contract");
  }

  return data;
}

function isDatabaseHealthResponse(
  value: unknown,
): value is DatabaseHealthResponse {
  if (typeof value !== "object" || value === null) {
    return false;
  }

  const response = value as Record<string, unknown>;
  return response.status === "ok" && response.database === "postgresql";
}

export async function getDatabaseHealth(
  signal?: AbortSignal,
): Promise<DatabaseHealthResponse> {
  const response = await fetch(`${apiBaseUrl}/api/health/database`, { signal });

  if (!response.ok) {
    throw new Error(
      `Database health request failed with status ${response.status}`,
    );
  }

  const data: unknown = await response.json();
  if (!isDatabaseHealthResponse(data)) {
    throw new Error("Database health response did not match the expected contract");
  }

  return data;
}

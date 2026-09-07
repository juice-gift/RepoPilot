export interface HealthResponse {
  status: "ok";
  service: "repopilot-api";
}

function isHealthResponse(value: unknown): value is HealthResponse {
  if (typeof value !== "object" || value === null) {
    return false;
  }

  const response = value as Record<string, unknown>;
  return response.status === "ok" && response.service === "repopilot-api";
}

export async function getHealth(signal?: AbortSignal): Promise<HealthResponse> {
  const response = await fetch("http://localhost:8000/api/health", { signal });

  if (!response.ok) {
    throw new Error(`Health request failed with status ${response.status}`);
  }

  const data: unknown = await response.json();
  if (!isHealthResponse(data)) {
    throw new Error("Health response did not match the expected contract");
  }

  return data;
}

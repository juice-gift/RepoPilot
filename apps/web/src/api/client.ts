export const apiBaseUrl = (
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000"
).replace(/\/$/, "");

export class ApiError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

export async function requestJson<T>(
  path: string,
  guard: (value: unknown) => value is T,
  init?: RequestInit,
): Promise<T> {
  const headers = new Headers(init?.headers);
  if (init?.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${apiBaseUrl}${path}`, {
    ...init,
    headers,
  });
  const data: unknown = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = isRecord(data) && typeof data.detail === "string"
      ? data.detail
      : `Request failed with status ${response.status}`;
    throw new ApiError(detail, response.status);
  }
  if (!guard(data)) {
    throw new Error("API response did not match the expected contract");
  }
  return data;
}

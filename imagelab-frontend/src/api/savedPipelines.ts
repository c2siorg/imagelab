import type {
  SavePipelineRequest,
  SavedPipelineResponse,
  SavedPipelineSummary,
} from "../types/pipeline";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:4100";

function getErrorDetail(data: unknown, status: number): string {
  if (typeof data === "object" && data !== null && "detail" in data) {
    const detail = (data as { detail?: unknown }).detail;
    if (typeof detail === "string") return detail;
  }
  return `Request failed: ${status}`;
}

async function requestJson<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}/api/pipelines${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  if (res.status === 204) {
    throw new Error("Unexpected empty response");
  }

  const data = await res.json();
  if (!res.ok) throw new Error(getErrorDetail(data, res.status));
  return data as T;
}

async function requestNoContent(path: string, options?: RequestInit): Promise<void> {
  const res = await fetch(`${API_URL}/api/pipelines${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  if (res.ok) return;

  const data = await res.json().catch(() => null);
  throw new Error(getErrorDetail(data, res.status));
}

export async function savePipeline(req: SavePipelineRequest): Promise<SavedPipelineResponse> {
  return requestJson<SavedPipelineResponse>("", { method: "POST", body: JSON.stringify(req) });
}

export async function listPipelines(): Promise<SavedPipelineSummary[]> {
  return requestJson<SavedPipelineSummary[]>("");
}

export async function getPipeline(id: number): Promise<SavedPipelineResponse> {
  return requestJson<SavedPipelineResponse>(`/${id}`);
}

export async function getPipelineByToken(token: string): Promise<SavedPipelineResponse> {
  return requestJson<SavedPipelineResponse>(`/share/${token}`);
}

export async function updatePipeline(
  id: number,
  req: SavePipelineRequest,
): Promise<SavedPipelineResponse> {
  return requestJson<SavedPipelineResponse>(`/${id}`, { method: "PUT", body: JSON.stringify(req) });
}

export async function deletePipeline(id: number): Promise<void> {
  return requestNoContent(`/${id}`, { method: "DELETE" });
}

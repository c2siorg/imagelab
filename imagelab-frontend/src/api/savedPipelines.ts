import type { SavePipelineRequest, SavedPipelineResponse, SavedPipelineSummary } from "../types/pipeline";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:4100";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}/api/pipelines${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (res.status === 204) return undefined as T;
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail ?? `Request failed: ${res.status}`);
  return data as T;
}

export async function savePipeline(req: SavePipelineRequest): Promise<SavedPipelineResponse> {
  return request<SavedPipelineResponse>("", { method: "POST", body: JSON.stringify(req) });
}

export async function listPipelines(): Promise<SavedPipelineSummary[]> {
  return request<SavedPipelineSummary[]>("");
}

export async function getPipeline(id: number): Promise<SavedPipelineResponse> {
  return request<SavedPipelineResponse>(`/${id}`);
}

export async function getPipelineByToken(token: string): Promise<SavedPipelineResponse> {
  return request<SavedPipelineResponse>(`/share/${token}`);
}

export async function updatePipeline(id: number, req: SavePipelineRequest): Promise<SavedPipelineResponse> {
  return request<SavedPipelineResponse>(`/${id}`, { method: "PUT", body: JSON.stringify(req) });
}

export async function deletePipeline(id: number): Promise<void> {
  return request<void>(`/${id}`, { method: "DELETE" });
}

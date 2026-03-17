import type { PipelineExportRequest, PipelineRequest, PipelineResponse } from "../types/pipeline";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:4100";

export async function executePipeline(request: PipelineRequest): Promise<PipelineResponse> {
  const response = await fetch(`${API_URL}/api/pipeline/execute`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
  return response.json();
}

export async function exportPipelineAsPython(request: PipelineExportRequest): Promise<string> {
  const response = await fetch(`${API_URL}/api/pipeline/export/python`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const errorBody = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new Error(errorBody?.detail || "Failed to export Python script");
  }

  return response.text();
}

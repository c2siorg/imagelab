import type { PipelineRequest, PipelineResponse, StepInspectResponse } from "../types/pipeline";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:4100";

export async function executePipeline(request: PipelineRequest): Promise<PipelineResponse> {
  const response = await fetch(`${API_URL}/api/v1/pipeline/executions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
  if (!response.ok) {
    throw new Error(`Pipeline execution failed with status ${response.status}`);
  }
  return response.json();
}

export async function inspectPipelineStep(
  executionId: string,
  blockId: string,
): Promise<StepInspectResponse> {
  const params = new URLSearchParams({ block_id: blockId });
  const response = await fetch(
    `${API_URL}/api/v1/pipeline/executions/${encodeURIComponent(executionId)}/steps/inspect?${params.toString()}`,
  );
  if (!response.ok) {
    throw new Error(`Step inspection failed with status ${response.status}`);
  }
  return response.json();
}

import type { PipelineRequest, PipelineResponse, StepInspectResponse } from "../types/pipeline";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:4100";

export interface PipelineExecutionError {
  step_id: string;
  step_type: string;
  message: string;
}

export class PipelineApiError extends Error {
  public readonly detail: PipelineExecutionError;
  constructor(detail: PipelineExecutionError) {
    super(detail.message);
    this.name = "PipelineApiError";
    this.detail = detail;
  }
}

function isPipelineExecutionError(data: unknown): data is PipelineExecutionError {
  if (typeof data !== "object" || data === null) return false;
  const candidate = data as Record<string, unknown>;
  return typeof candidate.step_type === "string" && typeof candidate.message === "string";
}

export async function executePipeline(request: PipelineRequest): Promise<PipelineResponse> {
  const response = await fetch(`${API_URL}/api/v1/pipeline/executions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
  if (!response.ok) {
    if (response.status === 400) {
      const errorData = await response.json().catch(() => null);
      if (isPipelineExecutionError(errorData)) {
        throw new PipelineApiError(errorData);
      }
      // Validation failures (e.g. a channel type mismatch) come back as a
      // PipelineResponse-shaped body with the message in `error`.
      const message =
        typeof errorData?.error === "string" && errorData.error
          ? errorData.error
          : `Pipeline execution failed with status ${response.status}`;
      throw new Error(message);
    }
    throw new Error(`Pipeline execution failed with status ${response.status}`);
  }
  return response.json();
}

export async function inspectPipelineStep(
  executionId: string,
  blockId: string,
): Promise<StepInspectResponse> {
  const params = new URLSearchParams({ block_id: encodeURIComponent(blockId) });
  const response = await fetch(
    `${API_URL}/api/v1/pipeline/executions/${encodeURIComponent(executionId)}/steps/inspect?${params.toString()}`,
  );
  if (!response.ok) {
    throw new Error(`Step inspection failed with status ${response.status}`);
  }
  return response.json();
}

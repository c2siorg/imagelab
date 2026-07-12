import type { BatchJobResponse, BatchJobSummary } from "../types/batch";
import type { PipelineStep } from "../types/pipeline";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:4100";

export async function createBatchJob(
  files: File[],
  pipeline: PipelineStep[],
  imageFormat: string = "png",
): Promise<BatchJobResponse> {
  const formData = new FormData();
  formData.append("pipeline", JSON.stringify(pipeline));
  formData.append("image_format", imageFormat);
  files.forEach((file) => {
    formData.append("files", file);
  });

  const response = await fetch(`${API_URL}/api/v1/batch-jobs`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const errData = await response.json().catch(() => ({}));
    throw new Error(errData.detail || `Failed to create batch job: ${response.status}`);
  }

  return response.json();
}

export async function getBatchJobStatus(jobId: string): Promise<BatchJobSummary> {
  const response = await fetch(`${API_URL}/api/v1/batch-jobs/${encodeURIComponent(jobId)}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch job status: ${response.status}`);
  }
  return response.json();
}

export function getBatchJobDownloadUrl(jobId: string): string {
  return `${API_URL}/api/v1/batch-jobs/${encodeURIComponent(jobId)}/download`;
}

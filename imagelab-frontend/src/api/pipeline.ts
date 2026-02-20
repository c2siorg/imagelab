import type { PipelineRequest, PipelineResponse } from '../types/pipeline';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:4100';

export async function executePipeline(request: PipelineRequest): Promise<PipelineResponse> {
  const response = await fetch(`${API_URL}/api/pipeline/execute`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
  return response.json();
}

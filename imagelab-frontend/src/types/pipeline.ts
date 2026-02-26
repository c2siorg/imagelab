export interface PipelineStep {
  type: string;
  params: Record<string, unknown>;
}

export interface PipelineRequest {
  image: string;
  image_format: string;
  pipeline: PipelineStep[];
}

export interface StepTiming {
  step: number;
  type: string;
  duration_ms: number;
}

export interface PipelineResponse {
  success: boolean;
  image?: string;
  image_format?: string;
  error?: string;
  step?: number;
  total_duration_ms?: number;
  step_timings?: StepTiming[];
}

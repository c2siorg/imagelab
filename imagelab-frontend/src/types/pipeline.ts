export interface PipelineStep {
  type: string;
  params: Record<string, unknown>;
}

export interface PipelineRequest {
  image: string;
  image_format: string;
  pipeline: PipelineStep[];
  include_intermediates?: boolean;
}

export interface StepTiming {
  step: number;
  operator_type: string;
  duration_ms: number;
}

export interface PipelineTimings {
  total_ms: number;
  steps: StepTiming[];
}

export interface ImageStats {
  width: number;
  height: number;
  channels: number;
  dtype: string;
  min_val: number;
  max_val: number;
  mean_val: number;
  histograms: number[][]; // one array for grayscale, three arrays for B/G/R (alpha excluded)
}

export interface StepResult {
  step: number;
  operator_type: string;
  thumbnail: string; // base64 JPEG
  stats: ImageStats;
}

export interface PipelineResponse {
  success: boolean;
  image?: string;
  image_format?: string;
  error?: string;
  step?: number;
  timings?: PipelineTimings;
  intermediates?: StepResult[];
}

// Saved pipeline types
export interface SavePipelineRequest {
  name: string;
  description?: string;
  pipeline_json: string;
  workspace_state?: string;
}

export interface SavedPipelineSummary {
  id: number;
  name: string;
  description: string;
  created_at: string;
  updated_at: string;
}

export interface SavedPipelineResponse extends SavedPipelineSummary {
  pipeline_json: string;
  workspace_state: string;
}

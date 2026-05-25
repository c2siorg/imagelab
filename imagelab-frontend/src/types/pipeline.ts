export interface PipelineStep {
  block_id?: string;
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
  operator_type: string;
  duration_ms: number;
}

export interface PipelineTimings {
  total_ms: number;
  steps: StepTiming[];
}

export interface StepResult {
  index: number;
  block_id?: string | null;
  type: string;
  success: boolean;
  thumbnail?: string | null;
  image_format?: string | null;
  timing_ms?: number | null;
  has_full_image: boolean;
  error?: string | null;
}

export interface ImageAnalysis {
  width: number;
  height: number;
  channels: number;
  dtype: string;
  min: number;
  max: number;
  mean: number | number[];
  std: number | number[];
}

export interface PipelineResponse {
  success: boolean;
  execution_id?: string | null;
  image?: string;
  image_format?: string;
  error?: string;
  step?: number;
  error_block_id?: string | null;
  timings?: PipelineTimings;
  step_results?: StepResult[];
}

export interface StepInspectResponse {
  success: boolean;
  execution_id: string;
  block_id: string;
  index: number;
  type: string;
  image: string;
  image_format: string;
  timing_ms?: number | null;
  analysis: ImageAnalysis;
}

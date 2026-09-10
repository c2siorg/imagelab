export interface BatchResultItem {
  filename: string;
  success: boolean;
  output_filename: string | null;
  error: string | null;
}

export interface BatchJobSummary {
  job_id: string;
  status: "pending" | "processing" | "completed" | "failed";
  total_files: number;
  processed_files: number;
  success_count: number;
  failure_count: number;
  created_at: number;
  updated_at: number;
  duration_seconds: number;
  results: BatchResultItem[];
}

export interface BatchJobResponse {
  job_id: string;
  status: string;
  total_files: number;
}

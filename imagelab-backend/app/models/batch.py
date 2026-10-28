from typing import Literal

from pydantic import BaseModel


class BatchResultItem(BaseModel):
    filename: str
    success: bool
    output_filename: str | None = None
    error: str | None = None


class BatchJobSummary(BaseModel):
    job_id: str
    status: Literal["pending", "processing", "completed", "failed"]
    total_files: int
    processed_files: int
    success_count: int
    failure_count: int
    created_at: float
    updated_at: float
    duration_seconds: float
    results: list[BatchResultItem] = []
    current_filename: str | None = None
    current_frame: int = 0
    total_frames_estimate: int | None = None


class BatchJobResponse(BaseModel):
    job_id: str
    status: str
    total_files: int

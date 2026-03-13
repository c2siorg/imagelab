"""Batch processing router — Feature 4.

Endpoints
---------
POST /api/batch/execute
    Accept a list of Base64-encoded images + a pipeline definition.
    Persist a :class:`~app.models.batch.BatchJob`, fire the execution as a
    :class:`~fastapi.BackgroundTasks` task, and return 202 Accepted with
    the ``job_id`` immediately — clients must **not** block on this call.

GET /api/batch/{job_id}/status
    Lightweight polling endpoint.  Returns the job and per-image statuses
    without the (potentially large) result image blobs so the response
    stays small even for large batches.

GET /api/batch/{job_id}/download
    Streams a ZIP archive containing every successfully processed image.
    Returns 409 Conflict if the job has not finished yet.
"""

import logging
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import Engine
from sqlmodel import Session, select

from app.database import get_db, get_engine
from app.models.batch import BatchItemResult, BatchJob, JobStatus
from app.models.pipeline import PipelineStep
from app.services.batch_service import build_zip, run_batch_job

logger = logging.getLogger(__name__)

router = APIRouter(tags=["batch"])

_MAX_BATCH_SIZE = 100


# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------


class BatchExecuteRequest(BaseModel):
    images: list[str] = Field(..., description="List of Base64-encoded input images.")
    image_format: str = Field("png", description="Output format: 'png', 'jpg', etc.")
    pipeline: list[PipelineStep] = Field(
        ..., description="Ordered list of pipeline steps (same format as /pipeline/execute)."
    )

    @field_validator("images")
    @classmethod
    def validate_images(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("images must contain at least one entry")
        if len(v) > _MAX_BATCH_SIZE:
            raise ValueError(f"Maximum {_MAX_BATCH_SIZE} images per batch")
        return v


class BatchExecuteResponse(BaseModel):
    job_id: uuid.UUID = Field(..., description="Unique ID for tracking the batch job.")
    total_images: int = Field(..., description="Number of images submitted.")
    message: str = Field(..., description="Status message and instructions.")


class ItemStatusResponse(BaseModel):
    index: int = Field(..., description="0-based index of the image in the batch.")
    status: str = Field(..., description="Processing status: 'pending', 'success', or 'failed'.")
    error: str | None = Field(None, description="Error message if status is 'failed'.")
    duration_ms: float | None = Field(None, description="Execution time in milliseconds.")


class BatchStatusResponse(BaseModel):
    job_id: uuid.UUID = Field(..., description="Unique job ID.")
    status: str = Field(..., description="Overall job status: 'pending', 'running', 'completed', or 'failed'.")
    total_images: int = Field(..., description="Total images in the batch.")
    completed_count: int = Field(..., description="Number of images processed successfully.")
    failed_count: int = Field(..., description="Number of images that failed.")
    items: list[ItemStatusResponse] = Field(..., description="Detail list for each image.")


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.post("/batch/execute", response_model=BatchExecuteResponse, status_code=202)
async def execute_batch(
    request: BatchExecuteRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),  # noqa: B008
    engine: Engine = Depends(get_engine),  # noqa: B008
) -> BatchExecuteResponse:
    """Submit a batch job and return immediately with a ``job_id``.

    The actual processing runs in the background via
    :func:`~app.services.batch_service.run_batch_job`.  Clients should
    poll ``GET /api/batch/{job_id}/status`` until ``status`` is
    ``"completed"`` or ``"failed"``, then call the download endpoint.

    This route is ``async def`` because it awaits FastAPI's background-task
    machinery.  The CPU-bound OpenCV work is dispatched to a thread pool
    inside :func:`~app.services.batch_service.run_batch_job`.
    """
    pipeline_steps_dict = [{"type": s.type, "params": s.params} for s in request.pipeline]

    job = BatchJob(
        total_images=len(request.images),
        image_format=request.image_format,
        pipeline_steps=pipeline_steps_dict,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    background_tasks.add_task(
        run_batch_job,
        job.id,
        request.images,
        request.image_format,
        pipeline_steps_dict,
        engine,
    )

    logger.info("Batch job %s submitted (%d images)", job.id, job.total_images)

    return BatchExecuteResponse(
        job_id=job.id,
        total_images=job.total_images,
        message=f"Batch job submitted. Poll GET /api/batch/{job.id}/status for progress.",
    )


@router.get("/batch/{job_id}/status", response_model=BatchStatusResponse)
def get_batch_status(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),  # noqa: B008
) -> BatchStatusResponse:
    """Return the current status and per-image progress for a batch job.

    This endpoint omits result image data to keep polling responses small.
    Plain ``def`` because it only does DB reads.
    """
    job = db.get(BatchJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Batch job not found")

    items = db.exec(
        select(BatchItemResult)
        .where(BatchItemResult.job_id == job_id)
        .order_by(BatchItemResult.image_index)
    ).all()

    return BatchStatusResponse(
        job_id=job.id,
        status=job.status,
        total_images=job.total_images,
        completed_count=job.completed_count,
        failed_count=job.failed_count,
        items=[
            ItemStatusResponse(
                index=item.image_index,
                status=item.status,
                error=item.error,
                duration_ms=item.duration_ms,
            )
            for item in items
        ],
    )


@router.get("/batch/{job_id}/download")
def download_batch_results(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),  # noqa: B008
) -> Response:
    """Stream a ZIP archive of all successfully processed images.

    Returns 409 Conflict while the job is still running or pending.
    Failed items are silently omitted from the archive; callers can check
    the ``/status`` endpoint to see which indices failed and why.
    """
    job = db.get(BatchJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Batch job not found")

    if job.status not in (JobStatus.completed, JobStatus.failed):
        raise HTTPException(
            status_code=409,
            detail=f"Job is still '{job.status}'. Call this endpoint only after the job completes.",
        )

    zip_bytes = build_zip(job_id, job.image_format, db)
    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=batch_{job_id}.zip"},
    )

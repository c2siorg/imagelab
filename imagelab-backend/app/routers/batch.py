import asyncio
import json
import os
import shutil
import time
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, Path, Request, UploadFile
from fastapi.responses import FileResponse
from pydantic import TypeAdapter

from app.models.batch import BatchJobResponse, BatchJobSummary
from app.models.graph import PipelineGraph
from app.models.pipeline import PipelineStep
from app.services.batch_executor import (
    JOBS_DIR,
    MAX_BATCH_UPLOAD_BYTES,
    MAX_VIDEO_UPLOAD_BYTES,
    cleanup_expired_batch_jobs,
    is_video_filename,
    run_batch_job,
    write_summary_atomic,
)

router = APIRouter()
JOB_ID_REGEX = r"^[a-zA-Z0-9_-]+$"


def _resolve_job_dir(job_id: str) -> str:
    """Safely resolve job directory, preventing path traversal outside JOBS_DIR."""
    job_dir = os.path.realpath(os.path.join(JOBS_DIR, job_id))
    jobs_root = os.path.realpath(JOBS_DIR)
    if not job_dir.startswith(jobs_root + os.sep) and job_dir != jobs_root:
        raise HTTPException(status_code=400, detail="Invalid job ID path")
    return job_dir


@router.post("/v1/batch-jobs", response_model=BatchJobResponse)
async def create_batch_job(
    request: Request,
    background_tasks: BackgroundTasks,
    pipeline: Annotated[str, Form(description="JSON string representing a PipelineGraph")],
    image_format: Annotated[str, Form(description="Format of the output images")] = "png",
    files: Annotated[list[UploadFile], File(description="Images to process")] = None,
):
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    content_length = request.headers.get("content-length")
    if content_length and content_length.isdigit() and int(content_length) > MAX_BATCH_UPLOAD_BYTES:
        max_mb = MAX_BATCH_UPLOAD_BYTES // (1024 * 1024)
        raise HTTPException(
            status_code=413,
            detail=f"Batch request exceeds the maximum allowed payload size of {max_mb} MB.",
        )

    try:
        raw_pipeline = json.loads(pipeline)
        if isinstance(raw_pipeline, list):
            # Preserve the pre-graph batch API for existing clients.
            steps = TypeAdapter(list[PipelineStep]).validate_python(raw_pipeline)
            pipeline_graph = PipelineGraph(
                nodes=[
                    {"id": step.block_id or str(index), "type": step.type, "params": step.params}
                    for index, step in enumerate(steps)
                ],
                edges=[
                    {"from": steps[index].block_id or str(index), "to": steps[index + 1].block_id or str(index + 1)}
                    for index in range(len(steps) - 1)
                ],
            )
        else:
            pipeline_graph = PipelineGraph.model_validate(raw_pipeline)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid pipeline JSON: {str(e)}") from e

    job_id = os.urandom(16).hex()
    job_dir = os.path.join(JOBS_DIR, job_id)
    inputs_dir = os.path.join(job_dir, "inputs")
    outputs_dir = os.path.join(job_dir, "outputs")

    os.makedirs(inputs_dir, exist_ok=True)
    os.makedirs(outputs_dir, exist_ok=True)

    def save_files():
        saved = []
        used_stems = set()
        total_request_bytes = 0
        for upload_file in files:
            if not upload_file.filename:
                continue
            filename = os.path.basename(upload_file.filename)
            stem, extension = os.path.splitext(filename)
            unique_stem = stem
            suffix = 1
            # adding number beside the image name to avoid overwriting images with same name
            while unique_stem.casefold() in used_stems:
                unique_stem = f"{stem}_{suffix}"
                suffix += 1
            used_stems.add(unique_stem.casefold())
            filename = f"{unique_stem}{extension}"
            dest_path = os.path.join(inputs_dir, filename)
            is_video = is_video_filename(filename)
            total_bytes = 0
            try:
                with open(dest_path, "wb") as f:
                    while chunk := upload_file.file.read(1024 * 1024):
                        chunk_len = len(chunk)
                        total_bytes += chunk_len
                        total_request_bytes += chunk_len
                        if total_request_bytes > MAX_BATCH_UPLOAD_BYTES:
                            max_mb = MAX_BATCH_UPLOAD_BYTES // (1024 * 1024)
                            raise HTTPException(
                                status_code=413,
                                detail=f"Total batch upload exceeds the maximum allowed size of {max_mb} MB.",
                            )
                        if is_video and total_bytes > MAX_VIDEO_UPLOAD_BYTES:
                            max_size_mb = MAX_VIDEO_UPLOAD_BYTES / (1024 * 1024)
                            max_size = (
                                f"{max_size_mb:g} MB"
                                if MAX_VIDEO_UPLOAD_BYTES >= 1024 * 1024
                                else f"{MAX_VIDEO_UPLOAD_BYTES} bytes"
                            )
                            raise HTTPException(
                                status_code=413,
                                detail=f"Video upload exceeds the maximum allowed size of {max_size}.",
                            )
                        f.write(chunk)
            except Exception:
                if os.path.exists(dest_path):
                    os.remove(dest_path)
                raise
            saved.append(filename)
        return saved

    try:
        filenames = await asyncio.to_thread(save_files)
    except HTTPException:
        shutil.rmtree(job_dir, ignore_errors=True)
        raise

    if not filenames:
        raise HTTPException(status_code=400, detail="No valid images or videos uploaded")

    t_now = time.time()
    summary = {
        "job_id": job_id,
        "status": "pending",
        "total_files": len(filenames),
        "processed_files": 0,
        "success_count": 0,
        "failure_count": 0,
        "created_at": t_now,
        "updated_at": t_now,
        "duration_seconds": 0.0,
        "results": [],
        "current_filename": None,
        "current_frame": 0,
        "total_frames_estimate": None,
    }
    await asyncio.to_thread(write_summary_atomic, job_id, summary)

    background_tasks.add_task(cleanup_expired_batch_jobs)
    background_tasks.add_task(run_batch_job, job_id, filenames, pipeline_graph, image_format)

    return BatchJobResponse(job_id=job_id, status="pending", total_files=len(filenames))


@router.get("/v1/batch-jobs/{job_id}", response_model=BatchJobSummary)
def get_batch_job_status(
    job_id: Annotated[str, Path(pattern=JOB_ID_REGEX, description="32-hex character batch job ID")],
):
    job_dir = _resolve_job_dir(job_id)
    summary_path = os.path.join(job_dir, "summary.json")
    if not os.path.exists(summary_path):
        raise HTTPException(status_code=404, detail="Batch job not found")

    try:
        with open(summary_path, encoding="utf-8") as f:
            data = json.load(f)
        return BatchJobSummary(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read job state: {str(e)}") from e


@router.get("/v1/batch-jobs/{job_id}/results")
def get_batch_job_results(
    job_id: Annotated[str, Path(pattern=JOB_ID_REGEX, description="32-hex character batch job ID")],
):
    job_dir = _resolve_job_dir(job_id)
    summary_path = os.path.join(job_dir, "summary.json")
    if not os.path.exists(summary_path):
        raise HTTPException(status_code=404, detail="Batch job not found")

    try:
        with open(summary_path, encoding="utf-8") as f:
            data = json.load(f)
        return {"job_id": job_id, "results": data.get("results", [])}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read job results: {str(e)}") from e


@router.get("/v1/batch-jobs/{job_id}/download")
def download_batch_results(
    job_id: Annotated[str, Path(pattern=JOB_ID_REGEX, description="32-hex character batch job ID")],
):
    job_dir = _resolve_job_dir(job_id)
    summary_path = os.path.join(job_dir, "summary.json")
    if not os.path.exists(summary_path):
        raise HTTPException(status_code=404, detail="Batch job not found")

    try:
        with open(summary_path, encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read job state: {str(e)}") from e

    status = data.get("status")
    if status not in ("completed", "failed"):
        raise HTTPException(status_code=400, detail="Batch job is still processing")

    zip_path = os.path.join(job_dir, "batch.zip")
    if not os.path.exists(zip_path):
        raise HTTPException(status_code=404, detail="ZIP bundle not found")

    return FileResponse(zip_path, media_type="application/zip", filename="batch.zip")

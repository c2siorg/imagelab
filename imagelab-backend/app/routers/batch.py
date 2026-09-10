import asyncio
import json
import os
import shutil
import time
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import TypeAdapter

from app.models.batch import BatchJobResponse, BatchJobSummary
from app.models.graph import PipelineGraph
from app.models.pipeline import PipelineStep
from app.services.batch_executor import JOBS_DIR, run_batch_job, write_summary_atomic

router = APIRouter()


@router.post("/v1/batch-jobs", response_model=BatchJobResponse)
async def create_batch_job(
    background_tasks: BackgroundTasks,
    pipeline: Annotated[str, Form(description="JSON string representing a PipelineGraph")],
    image_format: Annotated[str, Form(description="Format of the output images")] = "png",
    files: Annotated[list[UploadFile], File(description="Images to process")] = None,
):
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

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
        for upload_file in files:
            if not upload_file.filename:
                continue
            filename = os.path.basename(upload_file.filename)
            dest_path = os.path.join(inputs_dir, filename)
            with open(dest_path, "wb") as f:
                shutil.copyfileobj(upload_file.file, f)
            saved.append(filename)
        return saved

    filenames = await asyncio.to_thread(save_files)

    if not filenames:
        raise HTTPException(status_code=400, detail="No valid images uploaded")

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
    }
    await asyncio.to_thread(write_summary_atomic, job_id, summary)

    background_tasks.add_task(run_batch_job, job_id, filenames, pipeline_graph, image_format)

    return BatchJobResponse(job_id=job_id, status="pending", total_files=len(filenames))


@router.get("/v1/batch-jobs/{job_id}", response_model=BatchJobSummary)
def get_batch_job_status(job_id: str):
    summary_path = os.path.join(JOBS_DIR, job_id, "summary.json")
    if not os.path.exists(summary_path):
        raise HTTPException(status_code=404, detail="Batch job not found")

    try:
        with open(summary_path, encoding="utf-8") as f:
            data = json.load(f)
        return BatchJobSummary(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read job state: {str(e)}") from e


@router.get("/v1/batch-jobs/{job_id}/results")
def get_batch_job_results(job_id: str):
    summary_path = os.path.join(JOBS_DIR, job_id, "summary.json")
    if not os.path.exists(summary_path):
        raise HTTPException(status_code=404, detail="Batch job not found")

    try:
        with open(summary_path, encoding="utf-8") as f:
            data = json.load(f)
        return {"job_id": job_id, "results": data.get("results", [])}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read job results: {str(e)}") from e


@router.get("/v1/batch-jobs/{job_id}/download")
def download_batch_results(job_id: str):
    summary_path = os.path.join(JOBS_DIR, job_id, "summary.json")
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

    zip_path = os.path.join(JOBS_DIR, job_id, "batch.zip")
    if not os.path.exists(zip_path):
        raise HTTPException(status_code=404, detail="ZIP bundle not found")

    return FileResponse(zip_path, media_type="application/zip", filename="batch.zip")

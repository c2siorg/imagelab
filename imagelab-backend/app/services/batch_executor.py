import asyncio
import base64
import csv
import json
import logging
import os
import time
import zipfile

from app.models.pipeline import PipelineRequest, PipelineStep
from app.services.pipeline_executor import execute_pipeline

logger = logging.getLogger(__name__)

JOBS_DIR = os.path.abspath("jobs")
MAX_WORKERS = min(8, os.cpu_count() or 1)
semaphore = asyncio.Semaphore(MAX_WORKERS)


def write_summary_atomic(job_id: str, summary_data: dict):
    job_dir = os.path.join(JOBS_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)
    temp_path = os.path.join(job_dir, "summary.json.tmp")
    target_path = os.path.join(job_dir, "summary.json")
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2)
    os.replace(temp_path, target_path)


async def process_single_image(job_id: str, filename: str, pipeline: list[PipelineStep], image_format: str) -> dict:
    async with semaphore:
        try:

            def read_and_execute():
                input_path = os.path.join(JOBS_DIR, job_id, "inputs", filename)
                with open(input_path, "rb") as f:
                    image_bytes = f.read()

                image_b64 = base64.b64encode(image_bytes).decode("utf-8")

                req = PipelineRequest(image=image_b64, image_format=image_format, pipeline=pipeline)
                return execute_pipeline(req)

            response = await asyncio.to_thread(read_and_execute)

            if response.success and response.image:

                def save_output():
                    base_name, _ = os.path.splitext(filename)
                    out_ext = image_format.lower()
                    if out_ext == "jpg":
                        out_ext = "jpeg"
                    elif out_ext == "tif":
                        out_ext = "tiff"

                    out_filename = f"{base_name}_processed.{out_ext}"
                    out_path = os.path.join(JOBS_DIR, job_id, "outputs", out_filename)
                    os.makedirs(os.path.dirname(out_path), exist_ok=True)

                    img_data = base64.b64decode(response.image)
                    with open(out_path, "wb") as f:
                        f.write(img_data)
                    return out_filename

                out_filename = await asyncio.to_thread(save_output)
                return {"filename": filename, "success": True, "output_filename": out_filename, "error": None}
            else:
                return {
                    "filename": filename,
                    "success": False,
                    "output_filename": None,
                    "error": response.error or "Unknown pipeline execution error",
                }
        except Exception as e:
            logger.exception(f"Error processing image {filename} in job {job_id}")
            return {
                "filename": filename,
                "success": False,
                "output_filename": None,
                "error": f"Unexpected error: {str(e)}",
            }


async def run_batch_job(job_id: str, filenames: list[str], pipeline: list[PipelineStep], image_format: str):
    t_start = time.time()
    summary = {
        "job_id": job_id,
        "status": "processing",
        "total_files": len(filenames),
        "processed_files": 0,
        "success_count": 0,
        "failure_count": 0,
        "created_at": t_start,
        "updated_at": t_start,
        "duration_seconds": 0.0,
        "results": [],
    }
    await asyncio.to_thread(write_summary_atomic, job_id, summary)

    tasks = [process_single_image(job_id, fname, pipeline, image_format) for fname in filenames]
    success_count = 0
    failure_count = 0
    results = []

    for idx, future in enumerate(asyncio.as_completed(tasks), start=1):
        res = await future
        if res["success"]:
            success_count += 1
        else:
            failure_count += 1
        results.append(res)

        summary["processed_files"] = idx
        summary["success_count"] = success_count
        summary["failure_count"] = failure_count
        summary["updated_at"] = time.time()
        summary["duration_seconds"] = time.time() - t_start
        summary["results"] = results
        await asyncio.to_thread(write_summary_atomic, job_id, summary)

    final_status = "completed" if success_count > 0 else "failed"

    summary["status"] = final_status
    summary["updated_at"] = time.time()
    summary["duration_seconds"] = time.time() - t_start

    await asyncio.to_thread(write_summary_atomic, job_id, summary)

    if failure_count > 0:

        def write_errors():
            errors_path = os.path.join(JOBS_DIR, job_id, "errors.csv")
            with open(errors_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["filename", "error"])
                for r in results:
                    if not r["success"]:
                        writer.writerow([r["filename"], r["error"]])

        await asyncio.to_thread(write_errors)

    def create_zip_file():
        job_dir = os.path.join(JOBS_DIR, job_id)
        zip_path = os.path.join(job_dir, "batch.zip")
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            summary_path = os.path.join(job_dir, "summary.json")
            if os.path.exists(summary_path):
                zipf.write(summary_path, "summary.json")
            errors_path = os.path.join(job_dir, "errors.csv")
            if os.path.exists(errors_path):
                zipf.write(errors_path, "errors.csv")
            outputs_dir = os.path.join(job_dir, "outputs")
            if os.path.exists(outputs_dir):
                for root, _, files in os.walk(outputs_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.join("outputs", file)
                        zipf.write(file_path, arcname)

    await asyncio.to_thread(create_zip_file)

import asyncio
import base64
import csv
import json
import logging
import os
import shutil
import time
import zipfile

from app.database import engine
from app.exceptions import PipelineExecutionError
from app.models.graph import PipelineGraph
from app.models.pipeline import PipelineRequest
from app.services.graph_engine import compile_graph
from app.services.pipeline_executor import execute_pipeline

logger = logging.getLogger(__name__)


JOBS_DIR = os.path.abspath("jobs")
MAX_WORKERS = min(8, os.cpu_count() or 1)
semaphore = asyncio.Semaphore(MAX_WORKERS)
BATCH_JOB_TTL_SECONDS = int(os.getenv("BATCH_JOB_TTL_SECONDS", str(2 * 3600)))  # 2 hours default


def cleanup_expired_batch_jobs(max_age_seconds: int = BATCH_JOB_TTL_SECONDS, jobs_dir: str = JOBS_DIR) -> int:
    """Evict expired batch job directories from disk.

    Removes any job directory whose created_at timestamp or filesystem mtime
    exceeds max_age_seconds. Returns the count of removed directories.
    """
    if not os.path.exists(jobs_dir):
        return 0

    now = time.time()
    removed_count = 0

    try:
        entries = os.listdir(jobs_dir)
    except OSError as err:
        logger.warning(f"Could not list batch jobs directory '{jobs_dir}': {err}")
        return 0

    for entry in entries:
        job_dir = os.path.join(jobs_dir, entry)
        if not os.path.isdir(job_dir):
            continue

        job_age = None
        summary_path = os.path.join(job_dir, "summary.json")
        if os.path.exists(summary_path):
            try:
                with open(summary_path, encoding="utf-8") as f:
                    data = json.load(f)
                    created_at = data.get("created_at")
                    if isinstance(created_at, (int, float)):
                        job_age = now - created_at
            except Exception:
                pass

        if job_age is None:
            try:
                job_age = now - os.path.getmtime(job_dir)
            except OSError:
                continue

        if job_age > max_age_seconds:
            try:
                shutil.rmtree(job_dir, ignore_errors=True)
                removed_count += 1
                logger.info(f"Evicted expired batch job directory '{entry}' (age: {job_age:.1f}s)")
            except Exception as err:
                logger.warning(f"Failed to evict batch job directory '{entry}': {err}")

    return removed_count


def write_summary_atomic(job_id: str, summary_data: dict):
    job_dir = os.path.join(JOBS_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)
    temp_path = os.path.join(job_dir, "summary.json.tmp")
    target_path = os.path.join(job_dir, "summary.json")
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2)
    os.replace(temp_path, target_path)


async def process_single_image(job_id: str, filename: str, graph: PipelineGraph, image_format: str) -> dict:
    async with semaphore:
        try:

            def read_and_execute():
                input_path = os.path.join(JOBS_DIR, job_id, "inputs", filename)
                with open(input_path, "rb") as f:
                    image_bytes = f.read()

                image_b64 = base64.b64encode(image_bytes).decode("utf-8")

                from sqlmodel import Session

                from app.models.graph import PipelineGraph
                from app.services.graph_engine import _coerce_graph
                from app.utils.image import decode_base64_image

                image = decode_base64_image(image_b64)
                input_channels = 1 if image.ndim == 2 else image.shape[2]
                with Session(engine) as session:
                    # Handle both PipelineGraph and list (empty pipeline) cases
                    if isinstance(graph, PipelineGraph):
                        graph_dict = {
                            "nodes": [node.model_dump() for node in graph.nodes],
                            "edges": [edge.model_dump() for edge in graph.edges],
                        }
                        coerced_graph = _coerce_graph(graph_dict)
                        plan = compile_graph(coerced_graph, session, input_channels, [])
                    else:
                        # Empty pipeline case
                        plan = []
                req = PipelineRequest(image=image_b64, image_format=image_format, pipeline=plan)
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
        except PipelineExecutionError as e:
            return {
                "filename": filename,
                "success": False,
                "output_filename": None,
                "error": e.user_friendly_message,
            }
        except Exception as e:
            logger.exception(f"Error processing image {filename} in job {job_id}")
            return {
                "filename": filename,
                "success": False,
                "output_filename": None,
                "error": f"Unexpected error: {e}",
            }


async def run_batch_job(job_id: str, filenames: list[str], graph: PipelineGraph, image_format: str):
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

    tasks = [process_single_image(job_id, fname, graph, image_format) for fname in filenames]
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

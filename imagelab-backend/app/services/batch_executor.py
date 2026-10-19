import asyncio
import base64
import contextlib
import copy
import csv
import json
import logging
import math
import os
import shutil
import time
import zipfile
from collections.abc import Callable

import cv2
import numpy as np

from app.database import engine
from app.models.graph import PipelineGraph
from app.models.pipeline import PipelineRequest, PipelineStep
from app.services.graph_engine import compile_graph
from app.services.pipeline_executor import check_memory_limit, execute_pipeline, execute_pipeline_array

logger = logging.getLogger(__name__)


JOBS_DIR = os.path.abspath("jobs")
MAX_WORKERS = min(8, os.cpu_count() or 1)
semaphore = asyncio.Semaphore(MAX_WORKERS)
video_semaphore = asyncio.Semaphore(1)
VIDEO_EXTENSIONS = {".avi", ".m4v", ".mkv", ".mov", ".mp4", ".webm"}
MAX_VIDEO_UPLOAD_BYTES = 500 * 1024 * 1024
MAX_VIDEO_DURATION_SECONDS = 10 * 60
MAX_VIDEO_FRAMES = 18_000


def is_video_filename(filename: str) -> bool:
    return os.path.splitext(filename)[1].lower() in VIDEO_EXTENSIONS


def _compile_batch_pipeline(graph: PipelineGraph, input_channels: int) -> list[PipelineStep]:
    if not graph.nodes:
        return []

    from sqlmodel import Session

    from app.services.graph_engine import _coerce_graph

    graph_dict = {
        "nodes": [node.model_dump() for node in graph.nodes],
        "edges": [edge.model_dump() for edge in graph.edges],
    }
    with Session(engine) as session:
        return compile_graph(_coerce_graph(graph_dict), session, input_channels, [])


def _writer_frame(image: np.ndarray) -> np.ndarray:
    if image.dtype != np.uint8:
        raise ValueError(f"MP4 output requires 8-bit frames; pipeline returned {image.dtype}.")
    if image.ndim == 2:
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    elif image.ndim == 3 and image.shape[2] == 4:
        image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
    elif image.ndim != 3 or image.shape[2] != 3:
        raise ValueError("MP4 output requires grayscale, BGR, or BGRA frames.")
    return np.ascontiguousarray(image)


def _verify_mp4(path: str, width: int, height: int, expected_frames: int, expected_fps: float) -> None:
    capture = cv2.VideoCapture(path)
    if not capture.isOpened():
        capture.release()
        raise ValueError("OpenCV could not reopen the generated MP4; video encoding failed.")

    actual_fps = float(capture.get(cv2.CAP_PROP_FPS))
    if not math.isfinite(actual_fps) or not math.isclose(actual_fps, expected_fps, rel_tol=1e-3):
        capture.release()
        raise ValueError(f"MP4 writer changed the frame rate to {actual_fps}; expected {expected_fps}.")

    decoded_frames = 0
    try:
        while True:
            success, frame = capture.read()
            if not success:
                break
            if frame.shape[1] != width or frame.shape[0] != height:
                raise ValueError(
                    f"MP4 writer changed frame dimensions to {frame.shape[1]}x{frame.shape[0]}; "
                    f"expected {width}x{height}."
                )
            decoded_frames += 1
    finally:
        capture.release()

    if decoded_frames != expected_frames:
        raise ValueError(f"MP4 verification decoded {decoded_frames} of {expected_frames} written frames.")


def _process_video_file(
    job_id: str,
    filename: str,
    graph: PipelineGraph,
    progress_callback: Callable[[int, int | None], None],
) -> str:
    input_path = os.path.join(JOBS_DIR, job_id, "inputs", filename)
    base_name = os.path.splitext(filename)[0]
    output_filename = f"{base_name}_processed.mp4"
    outputs_dir = os.path.join(JOBS_DIR, job_id, "outputs")
    os.makedirs(outputs_dir, exist_ok=True)
    output_path = os.path.join(outputs_dir, output_filename)
    temp_path = os.path.join(outputs_dir, f".{base_name}_processed.tmp.mp4")

    capture = cv2.VideoCapture(input_path)
    if not capture.isOpened():
        capture.release()
        raise ValueError(f"Could not open video {filename}; the file may be unreadable or unsupported.")

    fps = float(capture.get(cv2.CAP_PROP_FPS))
    if not math.isfinite(fps) or fps <= 0:
        capture.release()
        raise ValueError(f"Could not determine a valid frame rate for video {filename}.")

    raw_frame_count = float(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    total_frames_estimate = (
        int(round(raw_frame_count)) if math.isfinite(raw_frame_count) and raw_frame_count > 0 else None
    )
    if total_frames_estimate is not None and total_frames_estimate > MAX_VIDEO_FRAMES:
        capture.release()
        raise ValueError(f"Video exceeds the maximum allowed frame count of {MAX_VIDEO_FRAMES}.")
    if total_frames_estimate is not None and total_frames_estimate / fps > MAX_VIDEO_DURATION_SECONDS:
        capture.release()
        raise ValueError(f"Video exceeds the maximum allowed duration of {MAX_VIDEO_DURATION_SECONDS} seconds.")
    writer = None
    frame_count = 0
    output_width = None
    output_height = None

    try:
        success, frame = capture.read()
        if not success:
            raise ValueError(f"Video {filename} contains no decodable frames.")

        pipeline = _compile_batch_pipeline(graph, 1 if frame.ndim == 2 else frame.shape[2])
        progress_callback(0, total_frames_estimate)
        while success:
            if frame_count >= MAX_VIDEO_FRAMES:
                raise ValueError(f"Video exceeds the maximum allowed frame count of {MAX_VIDEO_FRAMES}.")
            if (frame_count + 1) / fps > MAX_VIDEO_DURATION_SECONDS:
                raise ValueError(f"Video exceeds the maximum allowed duration of {MAX_VIDEO_DURATION_SECONDS} seconds.")
            check_memory_limit(frame)
            try:
                processed_image = execute_pipeline_array(frame, pipeline)
            except Exception as e:
                raise ValueError(f"Frame {frame_count + 1}: {e}") from e
            output_frame = _writer_frame(processed_image)
            check_memory_limit(output_frame)
            frame_height, frame_width = output_frame.shape[:2]
            if writer is None:
                output_width, output_height = frame_width, frame_height
                writer = cv2.VideoWriter(
                    temp_path,
                    cv2.VideoWriter_fourcc(*"mp4v"),
                    fps,
                    (output_width, output_height),
                )
                if not writer.isOpened():
                    writer.release()
                    writer = None
                    raise ValueError(
                        "OpenCV could not open an MP4 writer with the mp4v codec; "
                        "this installation may not support MP4 encoding."
                    )
            elif (frame_width, frame_height) != (output_width, output_height):
                raise ValueError(
                    f"Processed frame dimensions changed at frame {frame_count + 1}: "
                    f"expected {output_width}x{output_height}, got {frame_width}x{frame_height}."
                )

            writer.write(output_frame)
            frame_count += 1
            report_interval = max(1, round(fps / 2))
            if frame_count == 1 or frame_count % report_interval == 0:
                progress_callback(frame_count, total_frames_estimate)
            del output_frame, processed_image
            success, frame = capture.read()

        if writer is None or frame_count == 0:
            raise ValueError(f"Video {filename} contains no decodable frames.")
    except Exception:
        if writer is not None:
            writer.release()
            writer = None
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise
    finally:
        capture.release()
        if writer is not None:
            writer.release()

    try:
        _verify_mp4(temp_path, output_width, output_height, frame_count, fps)
        os.replace(temp_path, output_path)
    except Exception:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise
    return output_filename


async def process_single_video(
    job_id: str, filename: str, graph: PipelineGraph, progress_callback: Callable[[int, int | None], None]
) -> dict:
    async with video_semaphore, semaphore:
        try:
            progress_callback(0, None)
            output_filename = await asyncio.to_thread(_process_video_file, job_id, filename, graph, progress_callback)
            return {"filename": filename, "success": True, "output_filename": output_filename, "error": None}
        except Exception as e:
            logger.exception("Error processing video %s in job %s", filename, job_id)
            return {"filename": filename, "success": False, "output_filename": None, "error": str(e)}


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
        "current_filename": None,
        "current_frame": 0,
        "total_frames_estimate": None,
    }
    progress_queue: asyncio.Queue[tuple[str, int, int | None] | None] = asyncio.Queue(maxsize=1)
    summary_write_lock = asyncio.Lock()
    loop = asyncio.get_running_loop()

    async def persist_summary():
        async with summary_write_lock:
            await asyncio.to_thread(write_summary_atomic, job_id, copy.deepcopy(summary))

    async def persist_progress():
        while True:
            progress = await progress_queue.get()
            if progress is None:
                return
            filename, current_frame, total_frames_estimate = progress
            summary["current_filename"] = filename
            summary["current_frame"] = current_frame
            summary["total_frames_estimate"] = total_frames_estimate
            summary["updated_at"] = time.time()
            summary["duration_seconds"] = summary["updated_at"] - t_start
            await persist_summary()

    def write_progress(filename: str, current_frame: int, total_frames_estimate: int | None):
        def enqueue_latest():
            if progress_queue.full():
                with contextlib.suppress(asyncio.QueueEmpty):
                    progress_queue.get_nowait()
            progress_queue.put_nowait((filename, current_frame, total_frames_estimate))

        loop.call_soon_threadsafe(enqueue_latest)

    await persist_summary()
    progress_task = asyncio.create_task(persist_progress())

    tasks = [
        process_single_video(
            job_id,
            fname,
            graph,
            lambda frame, estimate, filename=fname: write_progress(filename, frame, estimate),
        )
        if is_video_filename(fname)
        else process_single_image(job_id, fname, graph, image_format)
        for fname in filenames
    ]
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
        if summary["current_filename"] == res["filename"]:
            summary["current_filename"] = None
            summary["current_frame"] = 0
            summary["total_frames_estimate"] = None
        await persist_summary()

    final_status = "completed" if success_count > 0 else "failed"
    await progress_queue.put(None)
    await progress_task
    summary["status"] = final_status
    summary["current_filename"] = None
    summary["current_frame"] = 0
    summary["total_frames_estimate"] = None
    summary["updated_at"] = time.time()
    summary["duration_seconds"] = time.time() - t_start
    await persist_summary()

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

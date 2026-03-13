"""Batch processing service — concurrently executes an image pipeline across
multiple input images, persisting progress to the database as each image
completes so the client can poll :func:`GET /api/batch/{job_id}/status`.

Concurrency model
-----------------
OpenCV operations are CPU-bound and synchronous.  This module submits each
image to a :class:`~concurrent.futures.ThreadPoolExecutor` (one thread per
image) and awaits all futures with :func:`asyncio.gather`, which keeps the
asyncio event loop free to serve other HTTP requests while the images are
being processed in parallel worker threads.

Thread-safety
-------------
All database writes use *separate* ``Session`` objects (one per commit)
created from the shared ``engine``.  The module-level ``_executor`` is safe
to share because ``execute_pipeline`` only mutates local variables.
"""

import asyncio
import base64
import io
import uuid
import zipfile
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import Engine
from sqlmodel import Session, select

from app.models.batch import BatchItemResult, BatchJob, ItemStatus, JobStatus
from app.models.pipeline import PipelineRequest, PipelineStep
from app.services.pipeline_executor import execute_pipeline

# Shared thread pool; size defaults to min(32, cpu_count + 4) in Python ≥3.8.
_executor: ThreadPoolExecutor = ThreadPoolExecutor()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _run_single(
    image_b64: str,
    image_format: str,
    steps: list[dict[str, Any]],
) -> tuple[bool, str | None, str | None, float]:
    """Execute *steps* against *image_b64* in a worker thread.

    Returns ``(success, result_b64, error_message, duration_ms)``.
    Designed to be called via :func:`loop.run_in_executor` — all state is
    local to this call, making it safe for concurrent use.
    """
    pipeline_steps = [PipelineStep(type=s["type"], params=s.get("params", {})) for s in steps]
    req = PipelineRequest(image=image_b64, image_format=image_format, pipeline=pipeline_steps)
    result = execute_pipeline(req)
    duration_ms = result.timings.total_ms if result.timings else 0.0
    return result.success, result.image, result.error, duration_ms


# ---------------------------------------------------------------------------
# Background worker
# ---------------------------------------------------------------------------


async def run_batch_job(
    job_id: uuid.UUID,
    images: list[str],
    image_format: str,
    pipeline_steps: list[dict[str, Any]],
    engine: Engine,
) -> None:
    """Async background task: process all *images* concurrently.

    This coroutine is wired up via FastAPI's ``BackgroundTasks`` immediately
    after the POST /batch/execute endpoint returns 202.  It:

    1. Marks the job *running* in the DB.
    2. Creates one :class:`BatchItemResult` row per image (status=pending).
    3. Fans out to the thread pool with :func:`asyncio.gather`.
    4. Writes each result back to the DB as images complete.
    5. Marks the job *completed* (or *failed* if every image failed).

    Parameters
    ----------
    engine:
        Injected via the ``get_engine`` FastAPI dependency so tests can
        substitute an in-memory SQLite engine without monkey-patching.
    """
    loop = asyncio.get_event_loop()

    # --- Phase 1: mark job running ---
    with Session(engine) as db:
        job = db.get(BatchJob, job_id)
        if job is None:
            return  # job was deleted before the task started
        job.status = JobStatus.running
        job.updated_at = datetime.now(UTC)
        db.add(job)
        db.commit()

    # --- Phase 2: pre-create pending item rows ---
    with Session(engine) as db:
        for i in range(len(images)):
            db.add(BatchItemResult(job_id=job_id, image_index=i, status=ItemStatus.pending))
        db.commit()

    # --- Phase 3: concurrent execution ---
    futures = [loop.run_in_executor(_executor, _run_single, img, image_format, pipeline_steps) for img in images]
    raw_results = await asyncio.gather(*futures, return_exceptions=True)

    # --- Phase 4: persist results ---
    completed_count = 0
    failed_count = 0

    with Session(engine) as db:
        for i, raw in enumerate(raw_results):
            item = db.exec(
                select(BatchItemResult).where(
                    BatchItemResult.job_id == job_id,
                    BatchItemResult.image_index == i,
                )
            ).first()
            if item is None:
                continue

            if isinstance(raw, Exception):
                item.status = ItemStatus.failed
                item.error = str(raw)
                failed_count += 1
            else:
                success, result_b64, error, duration_ms = raw
                if success:
                    item.status = ItemStatus.success
                    item.result_image_b64 = result_b64
                    item.duration_ms = duration_ms
                    completed_count += 1
                else:
                    item.status = ItemStatus.failed
                    item.error = error
                    item.duration_ms = duration_ms
                    failed_count += 1
            db.add(item)

        # --- Phase 5: mark job completed / failed ---
        job = db.get(BatchJob, job_id)
        if job:
            job.status = JobStatus.failed if completed_count == 0 else JobStatus.completed
            job.completed_count = completed_count
            job.failed_count = failed_count
            job.updated_at = datetime.now(UTC)
            db.add(job)
        db.commit()


# ---------------------------------------------------------------------------
# ZIP builder
# ---------------------------------------------------------------------------


def build_zip(job_id: uuid.UUID, image_format: str, db: Session) -> bytes:
    """Return an in-memory ZIP archive of every successful result image.

    Images are named ``result_0001.png``, ``result_0002.png``, … in
    ascending ``image_index`` order.  Failed items are silently omitted so
    the caller always gets a well-formed (possibly empty) ZIP.
    """
    items = db.exec(
        select(BatchItemResult)
        .where(
            BatchItemResult.job_id == job_id,
            BatchItemResult.status == ItemStatus.success,
        )
        .order_by(BatchItemResult.image_index)
    ).all()

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for item in items:
            if item.result_image_b64:
                img_bytes = base64.b64decode(item.result_image_b64)
                zf.writestr(f"result_{item.image_index + 1:04d}.{image_format}", img_bytes)
    return buf.getvalue()

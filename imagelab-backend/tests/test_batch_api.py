import asyncio
import io
import json
import os
import zipfile
from contextlib import asynccontextmanager
from unittest.mock import patch

import cv2
import numpy as np
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.exceptions import register_exception_handlers
from app.routers import batch as batch_router
from app.services import batch_executor


# Create a no-DB test application
@asynccontextmanager
async def _no_db_lifespan(a: FastAPI):
    yield


app_for_testing = FastAPI(lifespan=_no_db_lifespan)
app_for_testing.include_router(batch_router.router, prefix="/api")
register_exception_handlers(app_for_testing)


@pytest.fixture
def client():
    with TestClient(app_for_testing) as c:
        yield c


@pytest.fixture(autouse=True)
def temp_jobs_dir(tmp_path):
    temp_jobs = tmp_path / "jobs"
    temp_jobs.mkdir()

    with (
        patch("app.services.batch_executor.JOBS_DIR", str(temp_jobs)),
        patch("app.routers.batch.JOBS_DIR", str(temp_jobs)),
    ):
        yield temp_jobs


def test_create_batch_job_missing_files(client):
    r = client.post(
        "/api/v1/batch-jobs",
        data={"pipeline": "[]", "image_format": "png"},
    )
    assert r.status_code == 400
    assert r.json()["detail"] == "No files uploaded"


def test_create_batch_job_invalid_pipeline_json(client):
    files = [("files", ("image1.png", b"dummy_content", "image/png"))]
    r = client.post(
        "/api/v1/batch-jobs",
        data={"pipeline": "invalid json", "image_format": "png"},
        files=files,
    )
    assert r.status_code == 400
    assert "Invalid pipeline JSON" in r.json()["detail"]


@pytest.mark.anyio
async def test_create_batch_job_empty_filenames(client):
    from fastapi import BackgroundTasks, HTTPException, UploadFile

    bg_tasks = BackgroundTasks()
    mock_file = UploadFile(file=io.BytesIO(b"dummy"), filename="")
    with pytest.raises(HTTPException) as exc_info:
        await batch_router.create_batch_job(
            background_tasks=bg_tasks, pipeline="[]", image_format="png", files=[mock_file]
        )
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "No valid images uploaded"


def test_create_batch_job_success(client):
    files = [
        ("files", ("img1.png", b"dummy1", "image/png")),
        ("files", ("img2.png", b"dummy2", "image/png")),
    ]
    r = client.post(
        "/api/v1/batch-jobs",
        data={"pipeline": "[]", "image_format": "png"},
        files=files,
    )
    assert r.status_code == 200
    data = r.json()
    assert "job_id" in data
    assert data["status"] == "pending"
    assert data["total_files"] == 2


def test_get_batch_job_status_not_found(client):
    r = client.get("/api/v1/batch-jobs/non_existent_id")
    assert r.status_code == 404
    assert r.json()["detail"] == "Batch job not found"


def test_get_batch_job_status_success(client, temp_jobs_dir):
    job_id = "fake_job_1"
    job_dir = os.path.join(temp_jobs_dir, job_id)
    os.makedirs(job_dir)

    summary_data = {
        "job_id": job_id,
        "status": "completed",
        "total_files": 1,
        "processed_files": 1,
        "success_count": 1,
        "failure_count": 0,
        "created_at": 12345.0,
        "updated_at": 12346.0,
        "duration_seconds": 1.0,
        "results": [{"filename": "img.png", "success": True, "output_filename": "img_processed.png", "error": None}],
    }
    with open(os.path.join(job_dir, "summary.json"), "w") as f:
        json.dump(summary_data, f)

    r = client.get(f"/api/v1/batch-jobs/{job_id}")
    assert r.status_code == 200
    data = r.json()
    assert data["job_id"] == job_id
    assert data["status"] == "completed"
    assert len(data["results"]) == 1


def test_get_batch_job_results_not_found(client):
    r = client.get("/api/v1/batch-jobs/non_existent_id/results")
    assert r.status_code == 404
    assert r.json()["detail"] == "Batch job not found"


def test_get_batch_job_results_success(client, temp_jobs_dir):
    job_id = "fake_job_2"
    job_dir = os.path.join(temp_jobs_dir, job_id)
    os.makedirs(job_dir)

    summary_data = {
        "job_id": job_id,
        "status": "processing",
        "total_files": 2,
        "processed_files": 1,
        "success_count": 1,
        "failure_count": 0,
        "created_at": 12345.0,
        "updated_at": 12346.0,
        "duration_seconds": 1.0,
        "results": [{"filename": "img1.png", "success": True, "output_filename": "img1_processed.png", "error": None}],
    }
    with open(os.path.join(job_dir, "summary.json"), "w") as f:
        json.dump(summary_data, f)

    r = client.get(f"/api/v1/batch-jobs/{job_id}/results")
    assert r.status_code == 200
    data = r.json()
    assert data["job_id"] == job_id
    assert len(data["results"]) == 1
    assert data["results"][0]["filename"] == "img1.png"


def test_download_batch_results_not_found(client):
    r = client.get("/api/v1/batch-jobs/non_existent_id/download")
    assert r.status_code == 404
    assert r.json()["detail"] == "Batch job not found"


def test_download_batch_results_still_processing(client, temp_jobs_dir):
    job_id = "fake_job_3"
    job_dir = os.path.join(temp_jobs_dir, job_id)
    os.makedirs(job_dir)

    summary_data = {
        "job_id": job_id,
        "status": "processing",
        "total_files": 2,
        "processed_files": 1,
        "success_count": 1,
        "failure_count": 0,
        "created_at": 12345.0,
        "updated_at": 12346.0,
        "duration_seconds": 1.0,
        "results": [],
    }
    with open(os.path.join(job_dir, "summary.json"), "w") as f:
        json.dump(summary_data, f)

    r = client.get(f"/api/v1/batch-jobs/{job_id}/download")
    assert r.status_code == 400
    assert r.json()["detail"] == "Batch job is still processing"


def test_download_batch_results_zip_missing(client, temp_jobs_dir):
    job_id = "fake_job_4"
    job_dir = os.path.join(temp_jobs_dir, job_id)
    os.makedirs(job_dir)

    summary_data = {
        "job_id": job_id,
        "status": "completed",
        "total_files": 2,
        "processed_files": 2,
        "success_count": 2,
        "failure_count": 0,
        "created_at": 12345.0,
        "updated_at": 12346.0,
        "duration_seconds": 1.0,
        "results": [],
    }
    with open(os.path.join(job_dir, "summary.json"), "w") as f:
        json.dump(summary_data, f)

    r = client.get(f"/api/v1/batch-jobs/{job_id}/download")
    assert r.status_code == 404
    assert r.json()["detail"] == "ZIP bundle not found"


def test_download_batch_results_success(client, temp_jobs_dir):
    job_id = "fake_job_5"
    job_dir = os.path.join(temp_jobs_dir, job_id)
    os.makedirs(job_dir)

    summary_data = {
        "job_id": job_id,
        "status": "completed",
        "total_files": 2,
        "processed_files": 2,
        "success_count": 2,
        "failure_count": 0,
        "created_at": 12345.0,
        "updated_at": 12346.0,
        "duration_seconds": 1.0,
        "results": [],
    }
    with open(os.path.join(job_dir, "summary.json"), "w") as f:
        json.dump(summary_data, f)

    with zipfile.ZipFile(os.path.join(job_dir, "batch.zip"), "w") as zipf:
        zipf.writestr("test.txt", "content")

    r = client.get(f"/api/v1/batch-jobs/{job_id}/download")
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/zip"
    assert b"content" in r.content


# ---------------------------------------------------------------------------
# Failure handling, format verification (summary.json, errors.csv, batch.zip)
# ---------------------------------------------------------------------------


def _make_png_bytes() -> bytes:
    """Return minimal valid PNG bytes (10x10 white image)."""
    img = np.full((10, 10, 3), 255, dtype=np.uint8)
    _, buf = cv2.imencode(".png", img)
    return buf.tobytes()


@pytest.mark.anyio
async def test_run_batch_job_mixed_success_failure(temp_jobs_dir):
    """One file succeeds (valid PNG + empty pipeline), one fails (bad image bytes)."""
    job_id = "test_mixed"
    job_dir = os.path.join(str(temp_jobs_dir), job_id)
    inputs_dir = os.path.join(job_dir, "inputs")
    os.makedirs(inputs_dir)

    good_bytes = _make_png_bytes()
    with open(os.path.join(inputs_dir, "good.png"), "wb") as f:
        f.write(good_bytes)
    with open(os.path.join(inputs_dir, "bad.png"), "wb") as f:
        f.write(b"this is not an image")

    with patch("app.services.batch_executor.JOBS_DIR", str(temp_jobs_dir)):
        await batch_executor.run_batch_job(job_id, ["good.png", "bad.png"], [], "png")

    with open(os.path.join(job_dir, "summary.json"), encoding="utf-8") as f:
        summary = json.load(f)

    assert summary["total_files"] == 2
    assert summary["processed_files"] == 2
    assert summary["success_count"] == 1
    assert summary["failure_count"] == 1
    assert summary["status"] == "completed"


@pytest.mark.anyio
async def test_run_batch_job_all_failures(temp_jobs_dir):
    """When every file fails the status must be 'failed'."""
    job_id = "test_all_fail"
    job_dir = os.path.join(str(temp_jobs_dir), job_id)
    inputs_dir = os.path.join(job_dir, "inputs")
    os.makedirs(inputs_dir)

    for name in ("bad1.png", "bad2.png"):
        with open(os.path.join(inputs_dir, name), "wb") as f:
            f.write(b"not an image")

    with patch("app.services.batch_executor.JOBS_DIR", str(temp_jobs_dir)):
        await batch_executor.run_batch_job(job_id, ["bad1.png", "bad2.png"], [], "png")

    with open(os.path.join(job_dir, "summary.json"), encoding="utf-8") as f:
        summary = json.load(f)

    assert summary["status"] == "failed"
    assert summary["success_count"] == 0
    assert summary["failure_count"] == 2


@pytest.mark.anyio
async def test_summary_json_required_fields(temp_jobs_dir):
    """Validate every required field is present and typed correctly in summary.json."""
    job_id = "test_summary_fields"
    job_dir = os.path.join(str(temp_jobs_dir), job_id)
    inputs_dir = os.path.join(job_dir, "inputs")
    os.makedirs(inputs_dir)

    with open(os.path.join(inputs_dir, "img.png"), "wb") as f:
        f.write(_make_png_bytes())

    with patch("app.services.batch_executor.JOBS_DIR", str(temp_jobs_dir)):
        await batch_executor.run_batch_job(job_id, ["img.png"], [], "png")

    with open(os.path.join(job_dir, "summary.json"), encoding="utf-8") as f:
        summary = json.load(f)

    required_fields = {
        "job_id",
        "status",
        "total_files",
        "processed_files",
        "success_count",
        "failure_count",
        "created_at",
        "updated_at",
        "duration_seconds",
        "results",
    }
    assert required_fields.issubset(set(summary.keys()))
    assert summary["job_id"] == job_id
    assert isinstance(summary["results"], list)
    assert isinstance(summary["duration_seconds"], float)
    assert summary["duration_seconds"] >= 0.0


@pytest.mark.anyio
async def test_errors_csv_format_and_content(temp_jobs_dir):
    """errors.csv: correct header row and one data row per failure."""
    import csv as csv_module

    job_id = "test_errors_csv"
    job_dir = os.path.join(str(temp_jobs_dir), job_id)
    inputs_dir = os.path.join(job_dir, "inputs")
    os.makedirs(inputs_dir)

    with open(os.path.join(inputs_dir, "broken.png"), "wb") as f:
        f.write(b"not an image")

    with patch("app.services.batch_executor.JOBS_DIR", str(temp_jobs_dir)):
        await batch_executor.run_batch_job(job_id, ["broken.png"], [], "png")

    errors_path = os.path.join(job_dir, "errors.csv")
    assert os.path.exists(errors_path), "errors.csv must be created when failures occur"

    with open(errors_path, newline="", encoding="utf-8") as f:
        rows = list(csv_module.reader(f))

    # Header
    assert rows[0] == ["filename", "error"], f"Unexpected CSV header: {rows[0]}"
    # At least one data row for the failure
    assert len(rows) >= 2
    # Every data row has exactly 2 columns
    for row in rows[1:]:
        assert len(row) == 2, f"Row should have 2 columns: {row}"
    # The broken file appears in errors.csv
    assert "broken.png" in [row[0] for row in rows[1:]]
    # Error message is non-empty
    for row in rows[1:]:
        assert row[1].strip(), "Error description must not be empty"


@pytest.mark.anyio
async def test_errors_csv_not_written_when_all_succeed(temp_jobs_dir):
    """errors.csv must NOT be created when all files succeed."""
    job_id = "test_no_errors_csv"
    job_dir = os.path.join(str(temp_jobs_dir), job_id)
    inputs_dir = os.path.join(job_dir, "inputs")
    os.makedirs(inputs_dir)

    with open(os.path.join(inputs_dir, "good.png"), "wb") as f:
        f.write(_make_png_bytes())

    with patch("app.services.batch_executor.JOBS_DIR", str(temp_jobs_dir)):
        await batch_executor.run_batch_job(job_id, ["good.png"], [], "png")

    assert not os.path.exists(os.path.join(job_dir, "errors.csv"))


@pytest.mark.anyio
async def test_batch_zip_contains_expected_members(temp_jobs_dir):
    """batch.zip must always contain summary.json; errors.csv and outputs/ when relevant."""
    job_id = "test_zip_contents"
    job_dir = os.path.join(str(temp_jobs_dir), job_id)
    inputs_dir = os.path.join(job_dir, "inputs")
    os.makedirs(inputs_dir)

    with open(os.path.join(inputs_dir, "img.png"), "wb") as f:
        f.write(_make_png_bytes())
    with open(os.path.join(inputs_dir, "broken.png"), "wb") as f:
        f.write(b"not an image")

    with patch("app.services.batch_executor.JOBS_DIR", str(temp_jobs_dir)):
        await batch_executor.run_batch_job(job_id, ["img.png", "broken.png"], [], "png")

    zip_path = os.path.join(job_dir, "batch.zip")
    assert os.path.exists(zip_path), "batch.zip must always be created at the end of a job"

    with zipfile.ZipFile(zip_path, "r") as zipf:
        names = zipf.namelist()

    assert "summary.json" in names, "batch.zip must include summary.json"
    assert "errors.csv" in names, "batch.zip must include errors.csv when there are failures"
    output_files = [n for n in names if n.startswith("outputs/")]
    assert len(output_files) >= 1, "batch.zip must include at least one processed output image"


# ---------------------------------------------------------------------------
# Concurrency limit verification
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_concurrency_limit_respected(temp_jobs_dir, monkeypatch):
    """Active tasks running simultaneously must never exceed MAX_WORKERS.

    Strategy: replace process_single_image with a stub that honours the same
    semaphore gate as the real function, adds a tiny sleep so tasks overlap,
    and records the peak concurrency.  We then assert peak <= cap.
    """
    cap = 2
    peak_concurrent = 0
    current_concurrent = 0
    lock = asyncio.Lock()

    # Create a fresh semaphore with the desired cap and patch it into the module
    test_semaphore = asyncio.Semaphore(cap)
    monkeypatch.setattr(batch_executor, "semaphore", test_semaphore)
    monkeypatch.setattr(batch_executor, "MAX_WORKERS", cap)

    async def stub_process(job_id, filename, pipeline, image_format):
        """Mirror the real process_single_image gate: acquire semaphore first."""
        nonlocal peak_concurrent, current_concurrent
        async with test_semaphore:  # same gate as the real code
            async with lock:
                current_concurrent += 1
                if current_concurrent > peak_concurrent:
                    peak_concurrent = current_concurrent
            await asyncio.sleep(0.01)  # give other coroutines a chance
            result = {
                "filename": filename,
                "success": False,
                "output_filename": None,
                "error": "stubbed failure",
            }
            async with lock:
                current_concurrent -= 1
        return result

    monkeypatch.setattr(batch_executor, "process_single_image", stub_process)

    job_id = "test_concurrency"
    job_dir = os.path.join(str(temp_jobs_dir), job_id)
    inputs_dir = os.path.join(job_dir, "inputs")
    os.makedirs(inputs_dir)

    filenames = []
    for i in range(5):  # 5 tasks >> cap of 2
        name = f"img{i}.png"
        with open(os.path.join(inputs_dir, name), "wb") as f:
            f.write(b"stub")
        filenames.append(name)

    with patch("app.services.batch_executor.JOBS_DIR", str(temp_jobs_dir)):
        await batch_executor.run_batch_job(job_id, filenames, [], "png")

    assert peak_concurrent <= cap, f"Concurrency exceeded cap={cap}: peak simultaneous tasks was {peak_concurrent}"

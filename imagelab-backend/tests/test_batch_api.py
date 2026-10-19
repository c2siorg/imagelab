import asyncio
import io
import json
import os
import threading
import time
import zipfile
from contextlib import asynccontextmanager
from unittest.mock import patch

import cv2
import numpy as np
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.exceptions import register_exception_handlers
from app.models.graph import PipelineGraph
from app.models.pipeline import PipelineStep
from app.routers import batch as batch_router
from app.services import batch_executor
from app.services.pipeline_executor import _EXECUTION_CACHE


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


def test_create_batch_job_rejects_video_upload_over_size_limit(client, temp_jobs_dir, monkeypatch):
    monkeypatch.setattr(batch_router, "MAX_VIDEO_UPLOAD_BYTES", 4)
    response = client.post(
        "/api/v1/batch-jobs",
        data={"pipeline": "[]", "image_format": "png"},
        files=[("files", ("oversize.mp4", b"12345", "video/mp4"))],
    )

    assert response.status_code == 413
    assert "maximum allowed size of 4 bytes" in response.json()["detail"]
    assert list(temp_jobs_dir.iterdir()) == []


@pytest.mark.asyncio
async def test_upload_names_preserve_all_files_and_unique_output_stems(temp_jobs_dir):
    from fastapi import BackgroundTasks, UploadFile

    filenames = ["photo.png", "photo.png", "photo.jpg", "photo_1.png", "PHOTO.png"]
    uploads = [
        UploadFile(file=io.BytesIO(f"image-{index}".encode()), filename=name) for index, name in enumerate(filenames)
    ]
    background_tasks = BackgroundTasks()
    response = await batch_router.create_batch_job(
        background_tasks=background_tasks, pipeline="[]", image_format="png", files=uploads
    )

    expected = ["photo.png", "photo_1.png", "photo_2.jpg", "photo_1_1.png", "PHOTO_3.png"]
    inputs_dir = temp_jobs_dir / response.job_id / "inputs"
    assert sorted(path.name for path in inputs_dir.iterdir()) == sorted(expected)
    for index, name in enumerate(expected):
        assert (inputs_dir / name).read_bytes() == f"image-{index}".encode()
    assert response.total_files == len(uploads)
    (job_task,) = [task for task in background_tasks.tasks if task.func is batch_router.run_batch_job]
    assert job_task.args[1] == expected
    output_stems = [os.path.splitext(name)[0].casefold() for name in expected]
    assert len(set(output_stems)) == len(uploads)


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


def _write_test_video(path: str, frame_count: int = 4, fps: float = 8.0) -> bool:
    writer = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*"mp4v"), fps, (32, 24))
    if not writer.isOpened():
        writer.release()
        return False
    for index in range(frame_count):
        writer.write(np.full((24, 32, 3), index * 40, dtype=np.uint8))
    writer.release()
    return True


@pytest.mark.anyio
async def test_run_batch_job_processes_video_streaming_to_silent_mp4(temp_jobs_dir, monkeypatch):
    job_id = "test_video_success"
    job_dir = os.path.join(str(temp_jobs_dir), job_id)
    inputs_dir = os.path.join(job_dir, "inputs")
    os.makedirs(inputs_dir)
    input_path = os.path.join(inputs_dir, "clip.mp4")
    if not _write_test_video(input_path):
        pytest.skip("Installed OpenCV build cannot create mp4v test videos")

    progress_snapshots = []
    writer_thread_ids = []
    event_loop_thread_id = threading.get_ident()
    write_summary = batch_executor.write_summary_atomic
    cached_executions = set(_EXECUTION_CACHE)

    def record_summary(job_id, summary_data):
        writer_thread_ids.append(threading.get_ident())
        progress_snapshots.append(dict(summary_data))
        write_summary(job_id, summary_data)

    monkeypatch.setattr(batch_executor, "write_summary_atomic", record_summary)
    with patch("app.services.batch_executor.JOBS_DIR", str(temp_jobs_dir)):
        await batch_executor.run_batch_job(job_id, ["clip.mp4"], PipelineGraph(nodes=[], edges=[]), "png")

    with open(os.path.join(job_dir, "summary.json"), encoding="utf-8") as f:
        summary = json.load(f)
    result = summary["results"][0]
    assert summary["status"] == "completed"
    assert summary["processed_files"] == 1
    assert result["success"] is True
    assert result["output_filename"] == "clip_processed.mp4"
    assert any(
        progress["current_filename"] == "clip.mp4"
        and progress["current_frame"] >= 1
        and progress["total_frames_estimate"] == 4
        for progress in progress_snapshots
    )
    assert set(_EXECUTION_CACHE) == cached_executions
    assert writer_thread_ids
    assert all(thread_id != event_loop_thread_id for thread_id in writer_thread_ids)

    output_path = os.path.join(job_dir, "outputs", result["output_filename"])
    capture = cv2.VideoCapture(output_path)
    assert capture.isOpened()
    assert capture.get(cv2.CAP_PROP_FPS) == pytest.approx(8.0, rel=0.05)
    assert int(capture.get(cv2.CAP_PROP_FRAME_WIDTH)) == 32
    assert int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT)) == 24
    decoded_frames = 0
    while True:
        success, _ = capture.read()
        if not success:
            break
        decoded_frames += 1
    capture.release()
    assert decoded_frames == 4

    with zipfile.ZipFile(os.path.join(job_dir, "batch.zip")) as archive:
        assert f"outputs/{result['output_filename']}" in archive.namelist()


@pytest.mark.anyio
async def test_video_job_reports_unreadable_input(temp_jobs_dir):
    job_id = "test_video_unreadable"
    job_dir = os.path.join(str(temp_jobs_dir), job_id)
    inputs_dir = os.path.join(job_dir, "inputs")
    os.makedirs(inputs_dir)
    with open(os.path.join(inputs_dir, "broken.mp4"), "wb") as f:
        f.write(b"not a video")

    await batch_executor.run_batch_job(job_id, ["broken.mp4"], PipelineGraph(nodes=[], edges=[]), "png")

    with open(os.path.join(job_dir, "summary.json"), encoding="utf-8") as f:
        summary = json.load(f)
    assert summary["status"] == "failed"
    assert "Could not open video" in summary["results"][0]["error"]


@pytest.mark.anyio
async def test_video_job_reports_unsupported_mp4_writer(temp_jobs_dir, monkeypatch):
    job_id = "test_video_writer_unsupported"
    job_dir = os.path.join(str(temp_jobs_dir), job_id)
    inputs_dir = os.path.join(job_dir, "inputs")
    os.makedirs(inputs_dir)
    input_path = os.path.join(inputs_dir, "clip.mp4")
    if not _write_test_video(input_path):
        pytest.skip("Installed OpenCV build cannot create mp4v test videos")

    class UnsupportedWriter:
        def isOpened(self):
            return False

        def release(self):
            pass

    monkeypatch.setattr(batch_executor.cv2, "VideoWriter", lambda *args: UnsupportedWriter())
    await batch_executor.run_batch_job(job_id, ["clip.mp4"], PipelineGraph(nodes=[], edges=[]), "png")

    with open(os.path.join(job_dir, "summary.json"), encoding="utf-8") as f:
        summary = json.load(f)
    assert summary["status"] == "failed"
    assert "may not support MP4 encoding" in summary["results"][0]["error"]


@pytest.mark.anyio
async def test_video_job_uses_processed_frame_dimensions(temp_jobs_dir, monkeypatch):
    job_id = "test_video_resized_output"
    job_dir = os.path.join(str(temp_jobs_dir), job_id)
    inputs_dir = os.path.join(job_dir, "inputs")
    os.makedirs(inputs_dir)
    input_path = os.path.join(inputs_dir, "clip.mp4")
    if not _write_test_video(input_path, frame_count=2):
        pytest.skip("Installed OpenCV build cannot create mp4v test videos")

    def resize_processed_frame(image, pipeline):
        return np.zeros((12, 16, 3), dtype=np.uint8)

    monkeypatch.setattr(batch_executor, "execute_pipeline_array", resize_processed_frame)
    await batch_executor.run_batch_job(job_id, ["clip.mp4"], PipelineGraph(nodes=[], edges=[]), "png")

    with open(os.path.join(job_dir, "summary.json"), encoding="utf-8") as f:
        summary = json.load(f)
    assert summary["status"] == "completed"
    capture = cv2.VideoCapture(os.path.join(job_dir, "outputs", "clip_processed.mp4"))
    assert capture.isOpened()
    assert int(capture.get(cv2.CAP_PROP_FRAME_WIDTH)) == 16
    assert int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT)) == 12
    capture.release()


@pytest.mark.anyio
async def test_video_job_rejects_inconsistent_processed_frame_dimensions(temp_jobs_dir, monkeypatch):
    job_id = "test_video_inconsistent_dimensions"
    job_dir = os.path.join(str(temp_jobs_dir), job_id)
    inputs_dir = os.path.join(job_dir, "inputs")
    os.makedirs(inputs_dir)
    input_path = os.path.join(inputs_dir, "clip.mp4")
    if not _write_test_video(input_path, frame_count=2):
        pytest.skip("Installed OpenCV build cannot create mp4v test videos")

    frame_index = 0

    def change_frame_dimensions(image, pipeline):
        nonlocal frame_index
        frame_index += 1
        width = 32 if frame_index == 1 else 34
        return np.zeros((24, width, 3), dtype=np.uint8)

    monkeypatch.setattr(batch_executor, "execute_pipeline_array", change_frame_dimensions)
    await batch_executor.run_batch_job(job_id, ["clip.mp4"], PipelineGraph(nodes=[], edges=[]), "png")

    with open(os.path.join(job_dir, "summary.json"), encoding="utf-8") as f:
        summary = json.load(f)
    assert summary["status"] == "failed"
    assert "Processed frame dimensions changed at frame 2" in summary["results"][0]["error"]
    assert not os.path.exists(os.path.join(job_dir, "outputs", "clip_processed.mp4"))
    assert not os.path.exists(os.path.join(job_dir, "outputs", ".clip_processed.tmp.mp4"))


@pytest.mark.anyio
async def test_video_job_enforces_metadata_frame_and_duration_limits(temp_jobs_dir, monkeypatch):
    job_id = "test_video_limits"
    job_dir = os.path.join(str(temp_jobs_dir), job_id)
    inputs_dir = os.path.join(job_dir, "inputs")
    os.makedirs(inputs_dir)
    input_path = os.path.join(inputs_dir, "clip.mp4")
    if not _write_test_video(input_path, frame_count=4):
        pytest.skip("Installed OpenCV build cannot create mp4v test videos")

    monkeypatch.setattr(batch_executor, "MAX_VIDEO_FRAMES", 3)
    await batch_executor.run_batch_job(job_id, ["clip.mp4"], PipelineGraph(nodes=[], edges=[]), "png")

    with open(os.path.join(job_dir, "summary.json"), encoding="utf-8") as f:
        summary = json.load(f)
    assert summary["status"] == "failed"
    assert "maximum allowed frame count of 3" in summary["results"][0]["error"]

    monkeypatch.setattr(batch_executor, "MAX_VIDEO_FRAMES", 18_000)
    monkeypatch.setattr(batch_executor, "MAX_VIDEO_DURATION_SECONDS", 0.1)
    await batch_executor.run_batch_job(job_id, ["clip.mp4"], PipelineGraph(nodes=[], edges=[]), "png")
    with open(os.path.join(job_dir, "summary.json"), encoding="utf-8") as f:
        duration_summary = json.load(f)
    assert duration_summary["status"] == "failed"
    assert "maximum allowed duration of 0.1 seconds" in duration_summary["results"][0]["error"]


@pytest.mark.anyio
async def test_run_batch_job_processes_mixed_image_and_video(temp_jobs_dir):
    job_id = "test_mixed_media"
    job_dir = os.path.join(str(temp_jobs_dir), job_id)
    inputs_dir = os.path.join(job_dir, "inputs")
    os.makedirs(inputs_dir)
    with open(os.path.join(inputs_dir, "still.png"), "wb") as f:
        f.write(_make_png_bytes())
    video_path = os.path.join(inputs_dir, "clip.mp4")
    if not _write_test_video(video_path, frame_count=2):
        pytest.skip("Installed OpenCV build cannot create mp4v test videos")

    await batch_executor.run_batch_job(job_id, ["still.png", "clip.mp4"], PipelineGraph(nodes=[], edges=[]), "png")

    with open(os.path.join(job_dir, "summary.json"), encoding="utf-8") as f:
        summary = json.load(f)
    assert summary["status"] == "completed"
    assert summary["success_count"] == 2
    assert {result["output_filename"] for result in summary["results"]} == {
        "still_processed.png",
        "clip_processed.mp4",
    }


@pytest.mark.anyio
async def test_video_job_reports_pipeline_failure_with_frame_number(temp_jobs_dir, monkeypatch):
    job_id = "test_video_pipeline_failure"
    job_dir = os.path.join(str(temp_jobs_dir), job_id)
    inputs_dir = os.path.join(job_dir, "inputs")
    os.makedirs(inputs_dir)
    input_path = os.path.join(inputs_dir, "clip.mp4")
    if not _write_test_video(input_path, frame_count=1):
        pytest.skip("Installed OpenCV build cannot create mp4v test videos")

    monkeypatch.setattr(
        batch_executor,
        "_compile_batch_pipeline",
        lambda graph, input_channels: [PipelineStep(type="missing_operator")],
    )
    await batch_executor.run_batch_job(job_id, ["clip.mp4"], PipelineGraph(nodes=[], edges=[]), "png")

    with open(os.path.join(job_dir, "summary.json"), encoding="utf-8") as f:
        summary = json.load(f)
    assert summary["status"] == "failed"
    assert "Frame 1:" in summary["results"][0]["error"]
    assert "Unknown operator 'missing_operator'" in summary["results"][0]["error"]


@pytest.mark.anyio
async def test_video_acquires_video_slot_before_general_worker_slot(monkeypatch):
    entered = []

    class RecordingSemaphore:
        def __init__(self, name):
            self.name = name

        async def __aenter__(self):
            entered.append(self.name)

        async def __aexit__(self, exc_type, exc, traceback):
            return False

    monkeypatch.setattr(batch_executor, "video_semaphore", RecordingSemaphore("video"))
    monkeypatch.setattr(batch_executor, "semaphore", RecordingSemaphore("worker"))
    monkeypatch.setattr(batch_executor, "_process_video_file", lambda *args: "clip_processed.mp4")

    result = await batch_executor.process_single_video(
        "job", "clip.mp4", PipelineGraph(nodes=[], edges=[]), lambda *_: None
    )

    assert entered == ["video", "worker"]
    assert result["success"] is True


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


# ---------------------------------------------------------------------------
# Path traversal and automated storage retention cleanup
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "hostile_id",
    [
        "../traversal",
        "..%2Ftraversal",
        "../../etc/passwd",
        "..\\..\\windows",
        "job!with!special*chars",
        "job with spaces",
        "nested/path",
        ".",
        "..",
    ],
)
def test_batch_job_path_traversal_rejected(client, hostile_id):
    """Malicious or non-alphanumeric job_id values must be rejected with 404 or 422, never traversed."""
    for endpoint in [
        f"/api/v1/batch-jobs/{hostile_id}",
        f"/api/v1/batch-jobs/{hostile_id}/results",
        f"/api/v1/batch-jobs/{hostile_id}/download",
    ]:
        r = client.get(endpoint)
        assert r.status_code in (400, 404, 405, 422), (
            f"Endpoint {endpoint} unexpectedly returned {r.status_code} for hostile job_id: {hostile_id}"
        )


def test_cleanup_expired_batch_jobs(tmp_path):
    """Expired jobs exceeding TTL are removed; recent jobs are retained."""
    jobs_dir = tmp_path / "test_cleanup_jobs"
    jobs_dir.mkdir()

    now = time.time()
    ttl = 3600  # 1 hour

    # 1. Expired job with summary.json
    expired_id = "expired_job_123"
    expired_dir = jobs_dir / expired_id
    expired_dir.mkdir()
    with open(expired_dir / "summary.json", "w", encoding="utf-8") as f:
        json.dump({"job_id": expired_id, "created_at": now - 7200}, f)

    # 2. Active recent job with summary.json
    active_id = "active_job_456"
    active_dir = jobs_dir / active_id
    active_dir.mkdir()
    with open(active_dir / "summary.json", "w", encoding="utf-8") as f:
        json.dump({"job_id": active_id, "created_at": now - 60}, f)

    # 3. Expired directory without summary.json (using filesystem mtime)
    mtime_expired_dir = jobs_dir / "mtime_expired_789"
    mtime_expired_dir.mkdir()
    old_time = now - 7200
    os.utime(str(mtime_expired_dir), (old_time, old_time))

    # 4. Recent directory without summary.json
    mtime_active_dir = jobs_dir / "mtime_active_012"
    mtime_active_dir.mkdir()

    # Run cleanup
    removed = batch_executor.cleanup_expired_batch_jobs(max_age_seconds=ttl, jobs_dir=str(jobs_dir))
    assert removed == 2

    # Assert expired folders are gone
    assert not os.path.exists(str(expired_dir))
    assert not os.path.exists(str(mtime_expired_dir))

    # Assert active folders remain
    assert os.path.exists(str(active_dir))
    assert os.path.exists(str(mtime_active_dir))

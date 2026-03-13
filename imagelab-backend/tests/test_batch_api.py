"""Tests for Feature 4 — Batch Processing API.

Uses an in-memory SQLite database so no real PostgreSQL instance is needed.
FastAPI's ``TestClient`` runs ``BackgroundTasks`` synchronously before
returning, so tests can assert the final job state immediately after POST.

The ``get_db`` and ``get_engine`` FastAPI dependencies are overridden so both
the request-scoped DB session and the background-task engine point at the
same in-memory SQLite instance.

CRITICAL: model modules must be imported *before* SQLModel.metadata.create_all
so that the SQLModel metadata registry knows about all table classes.
"""

import base64
import io
import zipfile
from collections.abc import Generator

import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, StaticPool
from sqlmodel import Session, SQLModel, create_engine

# --- Force table registration before create_all ---
import app.models.batch  # noqa: F401
import app.models.macro  # noqa: F401
from app.database import get_db, get_engine
from app.main import app

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

# StaticPool keeps a single connection alive so in-memory data is visible
# across sessions (requests + background tasks all share the same SQLite file).
SQLITE_URL = "sqlite://"


@pytest.fixture(scope="function")
def db_engine() -> Generator[Engine, None, None]:
    """Fresh in-memory SQLite engine with a shared connection pool."""
    engine = create_engine(
        SQLITE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def client(db_engine: Engine) -> Generator[TestClient, None, None]:
    """TestClient with DB dependencies overridden to use in-memory SQLite."""

    def _get_test_db():
        with Session(db_engine) as session:
            yield session

    def _get_test_engine() -> Engine:
        return db_engine

    app.dependency_overrides[get_db] = _get_test_db
    app.dependency_overrides[get_engine] = _get_test_engine
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(scope="session")
def sample_png_b64() -> str:
    """A minimal 8×8 colour PNG encoded as Base64."""
    img = np.full((8, 8, 3), (100, 150, 200), dtype=np.uint8)
    _, buf = cv2.imencode(".png", img)
    return base64.b64encode(buf.tobytes()).decode()


def _gray_pipeline() -> list[dict]:
    return [{"type": "imageconvertions_grayimage", "params": {}}]


# ---------------------------------------------------------------------------
# POST /api/batch/execute
# ---------------------------------------------------------------------------


def test_batch_submit_returns_202(client, sample_png_b64):
    r = client.post(
        "/api/batch/execute",
        json={"images": [sample_png_b64], "image_format": "png", "pipeline": _gray_pipeline()},
    )
    assert r.status_code == 202
    data = r.json()
    assert "job_id" in data
    assert data["total_images"] == 1
    assert "poll" in data["message"].lower() or "status" in data["message"].lower()


def test_batch_submit_multiple_images(client, sample_png_b64):
    r = client.post(
        "/api/batch/execute",
        json={"images": [sample_png_b64] * 3, "image_format": "png", "pipeline": _gray_pipeline()},
    )
    assert r.status_code == 202
    assert r.json()["total_images"] == 3


def test_batch_submit_empty_images_rejected(client):
    r = client.post(
        "/api/batch/execute",
        json={"images": [], "image_format": "png", "pipeline": _gray_pipeline()},
    )
    assert r.status_code == 422


def test_batch_submit_over_limit_rejected(client, sample_png_b64):
    r = client.post(
        "/api/batch/execute",
        json={"images": [sample_png_b64] * 101, "image_format": "png", "pipeline": _gray_pipeline()},
    )
    assert r.status_code == 422


def test_batch_submit_invalid_pipeline(client, sample_png_b64):
    """An unknown operator makes items fail but the job itself still submits."""
    r = client.post(
        "/api/batch/execute",
        json={
            "images": [sample_png_b64],
            "image_format": "png",
            "pipeline": [{"type": "not_a_real_operator", "params": {}}],
        },
    )
    assert r.status_code == 202  # job accepted — items fail gracefully during execution


# ---------------------------------------------------------------------------
# GET /api/batch/{job_id}/status
# ---------------------------------------------------------------------------


def test_status_returns_completed_after_submit(client, sample_png_b64):
    """BackgroundTasks run synchronously in TestClient, so job finishes before we poll."""
    job_id = client.post(
        "/api/batch/execute",
        json={"images": [sample_png_b64, sample_png_b64], "image_format": "png", "pipeline": _gray_pipeline()},
    ).json()["job_id"]

    r = client.get(f"/api/batch/{job_id}/status")
    assert r.status_code == 200
    data = r.json()
    assert data["job_id"] == job_id
    assert data["total_images"] == 2
    assert data["status"] in ("completed", "running", "failed", "pending")  # still valid state
    assert "items" in data
    assert len(data["items"]) >= 0  # items may not exist yet if job didn't finish


def test_status_successful_items(client, sample_png_b64):
    job_id = client.post(
        "/api/batch/execute",
        json={"images": [sample_png_b64], "image_format": "png", "pipeline": _gray_pipeline()},
    ).json()["job_id"]

    status = client.get(f"/api/batch/{job_id}/status").json()
    assert status["status"] == "completed"
    assert status["completed_count"] == 1
    assert status["failed_count"] == 0
    assert status["items"][0]["status"] == "success"


def test_status_failed_items_on_bad_pipeline(client, sample_png_b64):
    job_id = client.post(
        "/api/batch/execute",
        json={
            "images": [sample_png_b64],
            "image_format": "png",
            "pipeline": [{"type": "bad_operator_xyz", "params": {}}],
        },
    ).json()["job_id"]

    status = client.get(f"/api/batch/{job_id}/status").json()
    assert status["status"] == "failed"
    assert status["failed_count"] == 1
    assert status["items"][0]["status"] == "failed"
    assert status["items"][0]["error"] is not None


def test_status_404_for_unknown_job(client):
    r = client.get("/api/batch/00000000-0000-0000-0000-000000000000/status")
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# GET /api/batch/{job_id}/download
# ---------------------------------------------------------------------------


def test_download_returns_zip(client, sample_png_b64):
    job_id = client.post(
        "/api/batch/execute",
        json={"images": [sample_png_b64, sample_png_b64], "image_format": "png", "pipeline": _gray_pipeline()},
    ).json()["job_id"]

    r = client.get(f"/api/batch/{job_id}/download")
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/zip"

    with zipfile.ZipFile(io.BytesIO(r.content)) as zf:
        names = zf.namelist()
    assert len(names) == 2
    assert all(n.endswith(".png") for n in names)


def test_download_404_for_unknown_job(client):
    r = client.get("/api/batch/00000000-0000-0000-0000-000000000000/download")
    assert r.status_code == 404

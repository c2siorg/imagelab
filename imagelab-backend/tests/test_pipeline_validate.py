"""Tests for Issue #197 — POST /api/pipeline/validate endpoint.

Uses a lightweight test app that skips DB migrations, matching the pattern
established in tests/test_pipeline_api.py and conftest.py.
"""

import base64
from contextlib import asynccontextmanager

import cv2
import numpy as np
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routers import pipeline as pipeline_router
from app.routers import validate as validate_router

# ---------------------------------------------------------------------------
# Minimal test app — no database needed for validation
# ---------------------------------------------------------------------------


@asynccontextmanager
async def _no_db_lifespan(a: FastAPI):
    yield


_test_app = FastAPI(lifespan=_no_db_lifespan)
_test_app.include_router(pipeline_router.router, prefix="/api")
_test_app.include_router(validate_router.router, prefix="/api")


@pytest.fixture(scope="module")
def client():
    with TestClient(_test_app) as c:
        yield c


@pytest.fixture(scope="module")
def sample_image_b64() -> str:
    img = np.full((10, 10, 3), 128, dtype=np.uint8)
    _, buf = cv2.imencode(".png", img)
    return base64.b64encode(buf.tobytes()).decode()


def _payload(steps: list[dict], image_b64: str) -> dict:
    return {"image": image_b64, "pipeline": steps}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_valid_single_operator(client, sample_image_b64):
    """A single known operator should return valid=True with no errors."""
    r = client.post(
        "/api/pipeline/validate",
        json=_payload([{"type": "imageconvertions_grayimage", "params": {}}], sample_image_b64),
    )
    assert r.status_code == 200
    body = r.json()
    assert body["valid"] is True
    assert body["errors"] == []


def test_valid_multi_step_pipeline(client, sample_image_b64):
    """Multiple known operators should all pass validation."""
    steps = [
        {"type": "imageconvertions_grayimage", "params": {}},
        {"type": "blurring_applygaussianblur", "params": {}},
        {"type": "filtering_sharpen", "params": {}},
    ]
    r = client.post("/api/pipeline/validate", json=_payload(steps, sample_image_b64))
    assert r.status_code == 200
    body = r.json()
    assert body["valid"] is True
    assert len(body["errors"]) == 0


def test_unknown_operator_returns_error(client, sample_image_b64):
    """A single unknown operator should return valid=False with one error."""
    r = client.post(
        "/api/pipeline/validate",
        json=_payload([{"type": "not_a_real_operator", "params": {}}], sample_image_b64),
    )
    assert r.status_code == 200
    body = r.json()
    assert body["valid"] is False
    assert len(body["errors"]) == 1
    assert body["errors"][0]["step"] == 1
    assert body["errors"][0]["operator"] == "not_a_real_operator"
    assert "not_a_real_operator" in body["errors"][0]["message"]


def test_mixed_valid_and_invalid_operators(client, sample_image_b64):
    """A pipeline with mixed known and unknown operators should report only the unknown ones."""
    steps = [
        {"type": "imageconvertions_grayimage", "params": {}},  # valid
        {"type": "completely_fake_op", "params": {}},           # invalid
        {"type": "blurring_applyblur", "params": {}},           # valid
        {"type": "another_fake_op", "params": {}},              # invalid
    ]
    r = client.post("/api/pipeline/validate", json=_payload(steps, sample_image_b64))
    assert r.status_code == 200
    body = r.json()
    assert body["valid"] is False
    assert len(body["errors"]) == 2
    assert body["errors"][0]["step"] == 2
    assert body["errors"][1]["step"] == 4


def test_empty_pipeline_returns_warning(client, sample_image_b64):
    """An empty pipeline should be valid but include a warning."""
    r = client.post("/api/pipeline/validate", json=_payload([], sample_image_b64))
    assert r.status_code == 200
    body = r.json()
    assert body["valid"] is True
    assert body["errors"] == []
    assert len(body["warnings"]) > 0
    assert any("empty" in w.lower() for w in body["warnings"])


def test_response_has_required_fields(client, sample_image_b64):
    """Response must always contain 'valid', 'warnings', and 'errors' keys."""
    r = client.post(
        "/api/pipeline/validate",
        json=_payload([{"type": "imageconvertions_grayimage", "params": {}}], sample_image_b64),
    )
    assert r.status_code == 200
    body = r.json()
    assert "valid" in body
    assert "warnings" in body
    assert "errors" in body


def test_error_object_has_step_operator_message(client, sample_image_b64):
    """Each error object must contain step, operator, and message fields."""
    r = client.post(
        "/api/pipeline/validate",
        json=_payload([{"type": "bad_op_xyz", "params": {}}], sample_image_b64),
    )
    assert r.status_code == 200
    err = r.json()["errors"][0]
    assert "step" in err
    assert "operator" in err
    assert "message" in err


def test_all_unknown_operators_marked(client, sample_image_b64):
    """Three unknown operators should produce three errors with correct step numbers."""
    steps = [
        {"type": "fake_a", "params": {}},
        {"type": "fake_b", "params": {}},
        {"type": "fake_c", "params": {}},
    ]
    r = client.post("/api/pipeline/validate", json=_payload(steps, sample_image_b64))
    body = r.json()
    assert body["valid"] is False
    assert len(body["errors"]) == 3
    assert [e["step"] for e in body["errors"]] == [1, 2, 3]


def test_validate_does_not_execute_pipeline(client, sample_image_b64):
    """Validate endpoint must not return an image — it only validates."""
    steps = [{"type": "imageconvertions_grayimage", "params": {}}]
    r = client.post("/api/pipeline/validate", json=_payload(steps, sample_image_b64))
    body = r.json()
    # The response must NOT contain an 'image' key (not a PipelineResponse)
    assert "image" not in body


def test_step_index_is_1_based(client, sample_image_b64):
    """Steps in error reports must be 1-indexed (first step = 1, not 0)."""
    steps = [{"type": "bad_op", "params": {}}]
    r = client.post("/api/pipeline/validate", json=_payload(steps, sample_image_b64))
    body = r.json()
    assert body["errors"][0]["step"] == 1

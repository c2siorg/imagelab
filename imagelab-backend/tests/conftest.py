import base64
from collections.abc import Callable
from contextlib import asynccontextmanager

import cv2
import numpy as np
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.models.pipeline import PipelineRequest, PipelineStep
from app.routers import pipeline as pipeline_router
from app.utils.image import encode_image_base64


@asynccontextmanager
async def _no_db_lifespan(a: FastAPI):
    # skip DB migrations in tests
    yield


_test_app = FastAPI(lifespan=_no_db_lifespan)
_test_app.include_router(pipeline_router.router, prefix="/api")


@pytest.fixture
def client():
    with TestClient(_test_app) as c:
        yield c


@pytest.fixture
def color_image():
    rng = np.random.default_rng(42)
    return rng.integers(0, 256, (100, 100, 3), dtype=np.uint8)


@pytest.fixture
def grayscale_image():
    rng = np.random.default_rng(42)
    return rng.integers(0, 256, (100, 100), dtype=np.uint8)


@pytest.fixture(scope="session")
def png_b64() -> str:
    img = np.zeros((10, 10, 3), dtype=np.uint8)
    img[:] = (100, 150, 200)
    _, buf = cv2.imencode(".png", img)
    return base64.b64encode(buf.tobytes()).decode()


@pytest.fixture(scope="session")
def sample_image_b64() -> str:
    img = np.full((100, 100, 3), 255, dtype=np.uint8)
    return encode_image_base64(img, "png")


@pytest.fixture
def make_request(sample_image_b64: str) -> Callable[[list[PipelineStep]], PipelineRequest]:
    def _make(steps: list[PipelineStep]) -> PipelineRequest:
        return PipelineRequest(image=sample_image_b64, pipeline=steps)

    return _make

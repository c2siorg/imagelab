import base64
from contextlib import asynccontextmanager

import cv2
import numpy as np
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routers import pipeline as pipeline_router


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


@pytest.fixture(scope="session")
def png_b64() -> str:
    img = np.zeros((10, 10, 3), dtype=np.uint8)
    img[:] = (100, 150, 200)
    _, buf = cv2.imencode(".png", img)
    return base64.b64encode(buf.tobytes()).decode()

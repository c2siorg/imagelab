import base64
from collections.abc import Callable

import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.database import get_db
from app.main import app
from app.models.pipeline import PipelineRequest, PipelineStep
from app.utils.image import encode_image_base64

# 1. In-memory SQLite engine using StaticPool for multi-thread stability
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@pytest.fixture(name="session")
def db_session_fixture():
    """Wipes and recreates tables per test to eliminate migration seed data."""
    SQLModel.metadata.drop_all(test_engine)
    SQLModel.metadata.create_all(test_engine)
    with Session(test_engine) as session:
        yield session
    SQLModel.metadata.drop_all(test_engine)


@pytest.fixture(name="client")
def client_fixture(session: Session):
    """Primary TestClient targeting app.main with overridden DB session."""

    def get_db_override():
        return session

    app.dependency_overrides[get_db] = get_db_override
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


# --- Image processing helper fixtures ---


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
def make_request(
    sample_image_b64: str,
) -> Callable[[list[PipelineStep]], PipelineRequest]:
    def _make(steps: list[PipelineStep]) -> PipelineRequest:
        return PipelineRequest(image=sample_image_b64, pipeline=steps)

    return _make

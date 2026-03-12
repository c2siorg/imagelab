"""Tests for Feature 5 — Macros CRUD API.

Uses an in-memory SQLite database — no PostgreSQL required.
All tests share a per-function engine so they are fully isolated.

CRITICAL: model modules must be imported *before* SQLModel.metadata.create_all
so that the SQLModel metadata registry knows about all table classes.
"""

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, StaticPool
from sqlmodel import Session, SQLModel, create_engine

# --- Force table registration before create_all ---
import app.models.batch  # noqa: F401
import app.models.macro  # noqa: F401

from app.database import get_db
from app.main import app

SQLITE_URL = "sqlite://"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function")
def db_engine() -> Engine:
    engine = create_engine(
        SQLITE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def client(db_engine: Engine) -> TestClient:
    def _get_test_db():
        with Session(db_engine) as session:
            yield session

    app.dependency_overrides[get_db] = _get_test_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _macro_payload(name: str = "Test Macro", steps: list | None = None) -> dict:
    if steps is None:
        steps = [
            {"type": "imageconvertions_grayimage", "params": {}},
            {"type": "blurring_applygaussianblur", "params": {"widthSize": 3, "heightSize": 3}},
        ]
    return {"name": name, "description": "A test macro", "steps": steps}


# ---------------------------------------------------------------------------
# POST /api/macros — create
# ---------------------------------------------------------------------------


def test_create_macro_returns_201(client):
    r = client.post("/api/macros", json=_macro_payload())
    assert r.status_code == 201
    data = r.json()
    assert "id" in data
    assert data["name"] == "Test Macro"
    assert data["step_count"] == 2
    assert len(data["steps"]) == 2


def test_create_macro_stores_steps_correctly(client):
    steps = [{"type": "imageconvertions_grayimage", "params": {}}]
    r = client.post("/api/macros", json=_macro_payload(steps=steps))
    assert r.status_code == 201
    data = r.json()
    assert data["steps"][0]["type"] == "imageconvertions_grayimage"


def test_create_macro_duplicate_name_returns_409(client):
    client.post("/api/macros", json=_macro_payload())
    r = client.post("/api/macros", json=_macro_payload())  # same name
    assert r.status_code == 409
    assert "already exists" in r.json()["detail"]


def test_create_macro_validates_name_not_empty(client):
    r = client.post("/api/macros", json={**_macro_payload(), "name": ""})
    assert r.status_code == 422


def test_create_macro_empty_steps_allowed(client):
    """A macro with zero steps is valid (empty composite block)."""
    r = client.post("/api/macros", json=_macro_payload(name="Empty", steps=[]))
    assert r.status_code == 201
    assert r.json()["step_count"] == 0


# ---------------------------------------------------------------------------
# GET /api/macros — list
# ---------------------------------------------------------------------------


def test_list_macros_initially_empty(client):
    r = client.get("/api/macros")
    assert r.status_code == 200
    assert r.json() == []


def test_list_macros_returns_all(client):
    client.post("/api/macros", json=_macro_payload("Alpha"))
    client.post("/api/macros", json=_macro_payload("Beta"))
    r = client.get("/api/macros")
    assert r.status_code == 200
    names = {m["name"] for m in r.json()}
    assert names == {"Alpha", "Beta"}


def test_list_macros_does_not_include_steps(client):
    """Summary endpoint should not return steps to keep payloads small."""
    client.post("/api/macros", json=_macro_payload())
    r = client.get("/api/macros")
    assert "steps" not in r.json()[0]


def test_list_macros_ordered_newest_first(client):
    client.post("/api/macros", json=_macro_payload("First"))
    client.post("/api/macros", json=_macro_payload("Second"))
    names = [m["name"] for m in client.get("/api/macros").json()]
    assert names[0] == "Second"  # newest first


# ---------------------------------------------------------------------------
# GET /api/macros/{id} — detail
# ---------------------------------------------------------------------------


def test_get_macro_returns_steps(client):
    macro_id = client.post("/api/macros", json=_macro_payload()).json()["id"]
    r = client.get(f"/api/macros/{macro_id}")
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == macro_id
    assert "steps" in data
    assert len(data["steps"]) == 2


def test_get_macro_404_for_unknown_id(client):
    r = client.get(f"/api/macros/{uuid.uuid4()}")
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# PUT /api/macros/{id} — update
# ---------------------------------------------------------------------------


def test_update_macro_name(client):
    macro_id = client.post("/api/macros", json=_macro_payload("Original")).json()["id"]
    r = client.put(f"/api/macros/{macro_id}", json={"name": "Renamed"})
    assert r.status_code == 200
    assert r.json()["name"] == "Renamed"


def test_update_macro_steps(client):
    macro_id = client.post("/api/macros", json=_macro_payload()).json()["id"]
    new_steps = [{"type": "imageconvertions_grayimage", "params": {}}]
    r = client.put(f"/api/macros/{macro_id}", json={"steps": new_steps})
    assert r.status_code == 200
    assert r.json()["step_count"] == 1


def test_update_macro_name_conflict_returns_409(client):
    client.post("/api/macros", json=_macro_payload("Taken"))
    macro_id = client.post("/api/macros", json=_macro_payload("Other")).json()["id"]
    r = client.put(f"/api/macros/{macro_id}", json={"name": "Taken"})
    assert r.status_code == 409


def test_update_macro_same_name_allowed(client):
    """Renaming a macro to its existing name must not raise a conflict."""
    created = client.post("/api/macros", json=_macro_payload("MyMacro")).json()
    r = client.put(f"/api/macros/{created['id']}", json={"name": "MyMacro"})
    assert r.status_code == 200


def test_update_macro_404_for_unknown_id(client):
    r = client.put(f"/api/macros/{uuid.uuid4()}", json={"name": "Ghost"})
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /api/macros/{id} — delete
# ---------------------------------------------------------------------------


def test_delete_macro_returns_204(client):
    macro_id = client.post("/api/macros", json=_macro_payload()).json()["id"]
    r = client.delete(f"/api/macros/{macro_id}")
    assert r.status_code == 204


def test_delete_macro_then_get_returns_404(client):
    macro_id = client.post("/api/macros", json=_macro_payload()).json()["id"]
    client.delete(f"/api/macros/{macro_id}")
    r = client.get(f"/api/macros/{macro_id}")
    assert r.status_code == 404


def test_delete_macro_removes_from_list(client):
    macro_id = client.post("/api/macros", json=_macro_payload()).json()["id"]
    client.delete(f"/api/macros/{macro_id}")
    assert client.get("/api/macros").json() == []


def test_delete_macro_404_for_unknown_id(client):
    r = client.delete(f"/api/macros/{uuid.uuid4()}")
    assert r.status_code == 404

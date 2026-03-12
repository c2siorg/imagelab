import json

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine, pool

from app.database import get_db
from app.main import app


@pytest.fixture(name="client")
def client_fixture():
    """TestClient backed by an in-memory SQLite database."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=pool.StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    def override_get_db():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


SAMPLE_PIPELINE = json.dumps([{"type": "blurring_applyblur", "params": {"widthSize": 3}}])


class TestSavePipeline:
    def test_save_returns_201(self, client):
        r = client.post("/api/pipelines", json={"name": "My Pipeline", "pipeline_json": SAMPLE_PIPELINE})
        assert r.status_code == 201

    def test_save_returns_id_and_share_token(self, client):
        r = client.post("/api/pipelines", json={"name": "Test", "pipeline_json": SAMPLE_PIPELINE})
        data = r.json()
        assert "id" in data
        assert "share_token" in data
        assert len(data["share_token"]) > 0

    def test_save_invalid_json_returns_422(self, client):
        r = client.post("/api/pipelines", json={"name": "Bad", "pipeline_json": "not-json{"})
        assert r.status_code == 422

    def test_save_rejects_oversized_workspace_state(self, client):
        huge = "x" * 1_000_001
        r = client.post(
            "/api/pipelines",
            json={"name": "Too Big", "pipeline_json": SAMPLE_PIPELINE, "workspace_state": huge},
        )
        assert r.status_code == 422


class TestListPipelines:
    def test_list_empty(self, client):
        r = client.get("/api/pipelines")
        assert r.status_code == 200
        assert r.json() == []

    def test_list_returns_saved_pipelines(self, client):
        client.post("/api/pipelines", json={"name": "P1", "pipeline_json": SAMPLE_PIPELINE})
        client.post("/api/pipelines", json={"name": "P2", "pipeline_json": SAMPLE_PIPELINE})
        r = client.get("/api/pipelines")
        assert len(r.json()) == 2

    def test_list_is_ordered_by_updated_at_desc(self, client):
        first = client.post("/api/pipelines", json={"name": "First", "pipeline_json": SAMPLE_PIPELINE}).json()
        second = client.post("/api/pipelines", json={"name": "Second", "pipeline_json": SAMPLE_PIPELINE}).json()
        client.put(
            f"/api/pipelines/{first['id']}",
            json={"name": "First Updated", "pipeline_json": SAMPLE_PIPELINE},
        )

        r = client.get("/api/pipelines")
        names = [p["name"] for p in r.json()]
        assert names[0] == "First Updated"
        assert "share_token" not in r.json()[0]
        assert second["name"] in names


class TestGetPipeline:
    def test_get_by_id(self, client):
        saved = client.post("/api/pipelines", json={"name": "Get Me", "pipeline_json": SAMPLE_PIPELINE}).json()
        r = client.get(f"/api/pipelines/{saved['id']}")
        assert r.status_code == 200
        assert r.json()["name"] == "Get Me"

    def test_get_nonexistent_returns_404(self, client):
        r = client.get("/api/pipelines/9999")
        assert r.status_code == 404

    def test_get_by_share_token(self, client):
        saved = client.post("/api/pipelines", json={"name": "Share Me", "pipeline_json": SAMPLE_PIPELINE}).json()
        token = saved["share_token"]
        r = client.get(f"/api/pipelines/share/{token}")
        assert r.status_code == 200
        assert r.json()["name"] == "Share Me"


class TestUpdatePipeline:
    def test_update_name(self, client):
        saved = client.post("/api/pipelines", json={"name": "Old Name", "pipeline_json": SAMPLE_PIPELINE}).json()
        r = client.put(f"/api/pipelines/{saved['id']}", json={"name": "New Name", "pipeline_json": SAMPLE_PIPELINE})
        assert r.status_code == 200
        assert r.json()["name"] == "New Name"

    def test_update_nonexistent_returns_404(self, client):
        r = client.put("/api/pipelines/9999", json={"name": "X", "pipeline_json": SAMPLE_PIPELINE})
        assert r.status_code == 404


class TestDeletePipeline:
    def test_delete_returns_204(self, client):
        saved = client.post("/api/pipelines", json={"name": "Del Me", "pipeline_json": SAMPLE_PIPELINE}).json()
        r = client.delete(f"/api/pipelines/{saved['id']}")
        assert r.status_code == 204

    def test_delete_then_get_returns_404(self, client):
        saved = client.post("/api/pipelines", json={"name": "Del Me", "pipeline_json": SAMPLE_PIPELINE}).json()
        client.delete(f"/api/pipelines/{saved['id']}")
        r = client.get(f"/api/pipelines/{saved['id']}")
        assert r.status_code == 404

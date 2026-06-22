import uuid
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.database import get_db
from app.main import app
from app.models.persistence import PipelineVersion

# Create an in-memory SQLite engine with StaticPool to keep the connection open
test_db_url = "sqlite://"
test_engine = create_engine(
    test_db_url,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@pytest.fixture(name="db_session")
def db_session_fixture():
    # Create the database tables
    SQLModel.metadata.create_all(test_engine)
    with Session(test_engine) as session:
        yield session
    # Drop tables after test
    SQLModel.metadata.drop_all(test_engine)


@pytest.fixture(name="client")
def client_fixture(db_session):
    def get_test_db():
        yield db_session

    # Override get_db in app dependencies
    app.dependency_overrides[get_db] = get_test_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


def test_pipeline_crud_and_versioning(client):
    # 1. Create pipeline (v1)
    payload = {
        "name": "My Pipeline",
        "workspace_json": {"blocks": [{"type": "read"}]},
        "pipeline_json": {"steps": []},
        "change_note": "Initial v1",
    }
    res = client.post("/api/pipelines/", json=payload)
    assert res.status_code == 201, res.text
    v1_data = res.json()
    pipeline_id = v1_data["pipeline_id"]
    assert v1_data["version_number"] == 1
    assert v1_data["change_note"] == "Initial v1"

    # 2. Get latest version of pipeline
    res = client.get(f"/api/pipelines/{pipeline_id}")
    assert res.status_code == 200
    assert res.json()["version_number"] == 1

    # 3. Create version 2
    res = client.post(
        f"/api/pipelines/{pipeline_id}/versions",
        json={
            "workspace_json": {"blocks": [{"type": "read"}, {"type": "blur"}]},
            "pipeline_json": {"steps": ["blur"]},
            "change_note": "Added blur v2",
        },
    )
    assert res.status_code == 201
    v2_data = res.json()
    assert v2_data["version_number"] == 2

    # 4. Get latest version again, verify it is v2
    res = client.get(f"/api/pipelines/{pipeline_id}")
    assert res.status_code == 200
    assert res.json()["version_number"] == 2

    # 5. List versions
    res = client.get(f"/api/pipelines/{pipeline_id}/versions")
    assert res.status_code == 200
    versions = res.json()
    assert len(versions) == 2
    assert versions[0]["version_number"] == 2
    assert versions[1]["version_number"] == 1

    # 6. Fetch specific version (v1)
    res = client.get(f"/api/pipelines/{pipeline_id}/versions/1")
    assert res.status_code == 200
    assert res.json()["change_note"] == "Initial v1"

    # 7. Restore v1 (creates v3 with same layout)
    res = client.post(f"/api/pipelines/{pipeline_id}/restore/1")
    assert res.status_code == 201
    v3_data = res.json()
    assert v3_data["version_number"] == 3
    assert v3_data["change_note"] == "Restored from v1"
    assert v3_data["workspace_json"] == {"blocks": [{"type": "read"}]}

    # 8. Delete pipeline
    res = client.delete(f"/api/pipelines/{pipeline_id}")
    assert res.status_code == 204
    res = client.get(f"/api/pipelines/{pipeline_id}")
    assert res.status_code == 404


def test_concurrency_conflict(client, db_session):
    # Create initial pipeline
    payload = {"name": "Race Pipeline", "workspace_json": {}, "pipeline_json": {}, "change_note": "v1"}
    res = client.post("/api/pipelines/", json=payload)
    pipeline_id = res.json()["pipeline_id"]

    # Directly insert a version 2 in db to simulate a concurrent save success
    db_session.add(
        PipelineVersion(pipeline_id=uuid.UUID(pipeline_id), version_number=2, workspace_json={}, pipeline_json={})
    )
    db_session.commit()

    # Verify that trying to insert a duplicate version 2 triggers unique constraint
    dup_version = PipelineVersion(
        pipeline_id=uuid.UUID(pipeline_id), version_number=2, workspace_json={}, pipeline_json={}
    )
    db_session.add(dup_version)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_pipeline_sharing_and_cloning(client):
    # 1. Setup pipeline & version
    payload = {
        "name": "Sharable Pipeline",
        "workspace_json": {"blocks": [{"type": "read"}]},
        "pipeline_json": {},
        "change_note": "v1",
    }
    res = client.post("/api/pipelines/", json=payload)
    v1_data = res.json()
    pipeline_id = v1_data["pipeline_id"]

    # 2. Share with Clone permission
    res = client.post(f"/api/pipelines/{pipeline_id}/share", json={"version_number": 1, "permission": "clone"})
    assert res.status_code == 201
    raw_token = res.json()["token"]
    assert isinstance(raw_token, str)

    # 3. Lookup the share link
    res = client.get(f"/api/share/{raw_token}")
    assert res.status_code == 200
    lookup_data = res.json()
    assert lookup_data["pipeline_name"] == "Sharable Pipeline"
    assert lookup_data["permission"] == "clone"
    assert lookup_data["workspace_json"] == {"blocks": [{"type": "read"}]}

    # 4. Clone the pipeline
    res = client.post(f"/api/share/{raw_token}/clone", json={"name": "My Cloned Pipeline", "owner_id": "user123"})
    assert res.status_code == 201
    cloned_version = res.json()
    assert cloned_version["version_number"] == 1
    assert cloned_version["change_note"].startswith("Cloned from Sharable Pipeline")

    # Verify the clone exists in the database
    new_pipeline_id = cloned_version["pipeline_id"]
    res = client.get(f"/api/pipelines/{new_pipeline_id}")
    assert res.status_code == 200


def test_share_obfuscation_and_expiry(client):
    # 1. Setup pipeline
    payload = {"name": "Private Pipeline", "workspace_json": {}, "pipeline_json": {}, "change_note": "v1"}
    res = client.post("/api/pipelines/", json=payload)
    pipeline_id = res.json()["pipeline_id"]

    # 2. Share with expired date
    expired_at = datetime.now(UTC) - timedelta(minutes=1)
    res = client.post(
        f"/api/pipelines/{pipeline_id}/share",
        json={"version_number": 1, "permission": "view", "expires_at": expired_at.isoformat()},
    )
    expired_token = res.json()["token"]

    # 3. Lookup expired share token - should return 404 with generic message
    res = client.get(f"/api/share/{expired_token}")
    assert res.status_code == 404
    assert res.json()["detail"] == "Invalid or expired share link"

    # 4. Try to clone expired share token - should return 404 with generic message
    res = client.post(f"/api/share/{expired_token}/clone", json={})
    assert res.status_code == 404
    assert res.json()["detail"] == "Invalid or expired share link"

    # 5. Lookup non-existent token - should return 404 with identical message (obfuscation)
    res = client.get("/api/share/non-existent-token-12345")
    assert res.status_code == 404
    assert res.json()["detail"] == "Invalid or expired share link"

    # 6. Share with "view" only permission and try to clone
    res = client.post(f"/api/pipelines/{pipeline_id}/share", json={"version_number": 1, "permission": "view"})
    view_token = res.json()["token"]
    res = client.post(f"/api/share/{view_token}/clone", json={})
    assert res.status_code == 403
    assert res.json()["detail"] == "Cloning not permitted for this share link"


def test_rate_limiting(client):
    blocked = False
    for _i in range(35):
        res = client.get("/api/share/dummy-token")
        if res.status_code == 429:
            blocked = True
            assert res.json()["detail"] == "Too many requests. Please try again later."
            break
    assert blocked, "Rate limiter did not block request after 30 hits"

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from app.database import get_db
from app.main import app
from app.middleware.rate_limit import reset_share_rate_limit_state
from app.models.persistence import PipelineShare, PipelineVersion
from app.routers import persistence as persistence_router

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


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    reset_share_rate_limit_state()
    yield
    reset_share_rate_limit_state()


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


def test_create_version_conflict_returns_409(client, db_session):
    """Simulate a lost race: two saves both compute the same next version number."""
    payload = {"name": "Conflict Pipeline", "workspace_json": {"v": 1}, "pipeline_json": {}, "change_note": "v1"}
    res = client.post("/api/pipelines/", json=payload)
    pipeline_id = res.json()["pipeline_id"]

    db_session.add(
        PipelineVersion(
            pipeline_id=uuid.UUID(pipeline_id),
            version_number=2,
            workspace_json={"v": 2},
            pipeline_json={},
        )
    )
    db_session.commit()

    with patch.object(persistence_router, "_next_version_number", return_value=2):
        res = client.post(
            f"/api/pipelines/{pipeline_id}/versions",
            json={"workspace_json": {"v": "race"}, "pipeline_json": {}, "change_note": "lost race"},
        )

    assert res.status_code == 409
    assert res.json()["detail"] == "Version conflict – please retry"


def test_restore_version_conflict_returns_409(client, db_session):
    payload = {"name": "Restore Conflict", "workspace_json": {"v": 1}, "pipeline_json": {}, "change_note": "v1"}
    res = client.post("/api/pipelines/", json=payload)
    pipeline_id = res.json()["pipeline_id"]

    db_session.add(
        PipelineVersion(
            pipeline_id=uuid.UUID(pipeline_id),
            version_number=2,
            workspace_json={"v": 2},
            pipeline_json={},
        )
    )
    db_session.commit()

    with patch.object(persistence_router, "_next_version_number", return_value=2):
        res = client.post(f"/api/pipelines/{pipeline_id}/restore/1")

    assert res.status_code == 409
    assert res.json()["detail"] == "Version conflict – please retry"


def test_list_pipelines(client):
    for name in ("Alpha", "Beta"):
        client.post(
            "/api/pipelines/",
            json={"name": name, "workspace_json": {}, "pipeline_json": {}, "change_note": "v1"},
        )

    res = client.get("/api/pipelines/")
    assert res.status_code == 200
    names = {p["name"] for p in res.json()}
    assert names == {"Alpha", "Beta"}


def test_pipeline_not_found_errors(client):
    missing_id = str(uuid.uuid4())

    assert client.get(f"/api/pipelines/{missing_id}").status_code == 404
    assert client.delete(f"/api/pipelines/{missing_id}").status_code == 404
    assert client.get(f"/api/pipelines/{missing_id}/versions").status_code == 404
    assert (
        client.post(
            f"/api/pipelines/{missing_id}/versions", json={"workspace_json": {}, "pipeline_json": {}}
        ).status_code
        == 404
    )
    assert client.get(f"/api/pipelines/{missing_id}/versions/1").status_code == 404
    assert client.post(f"/api/pipelines/{missing_id}/restore/1").status_code == 404
    assert (
        client.post(
            f"/api/pipelines/{missing_id}/share",
            json={"version_number": 1, "permission": "view"},
        ).status_code
        == 404
    )


def test_version_not_found_errors(client):
    res = client.post(
        "/api/pipelines/",
        json={"name": "Version Errors", "workspace_json": {}, "pipeline_json": {}, "change_note": "v1"},
    )
    pipeline_id = res.json()["pipeline_id"]

    assert client.get(f"/api/pipelines/{pipeline_id}/versions/99").status_code == 404
    assert client.post(f"/api/pipelines/{pipeline_id}/restore/99").status_code == 404
    assert (
        client.post(
            f"/api/pipelines/{pipeline_id}/share",
            json={"version_number": 99, "permission": "view"},
        ).status_code
        == 404
    )


def test_clone_default_name(client):
    res = client.post(
        "/api/pipelines/",
        json={"name": "Original", "workspace_json": {"blocks": []}, "pipeline_json": {}, "change_note": "v1"},
    )
    pipeline_id = res.json()["pipeline_id"]

    share_res = client.post(
        f"/api/pipelines/{pipeline_id}/share",
        json={"version_number": 1, "permission": "clone"},
    )
    token = share_res.json()["token"]

    clone_res = client.post(f"/api/share/{token}/clone", json={})
    assert clone_res.status_code == 201
    cloned = clone_res.json()
    assert cloned["version_number"] == 1
    assert cloned["change_note"] == "Cloned from Original (v1)"

    pipelines = client.get("/api/pipelines/").json()
    cloned_meta = next(p for p in pipelines if p["id"] == cloned["pipeline_id"])
    assert cloned_meta["name"] == "Clone of Original"


def test_share_after_pipeline_deleted_returns_obfuscated_404(client, db_session):
    res = client.post(
        "/api/pipelines/",
        json={"name": "Ephemeral", "workspace_json": {}, "pipeline_json": {}, "change_note": "v1"},
    )
    pipeline_id = res.json()["pipeline_id"]

    share_res = client.post(
        f"/api/pipelines/{pipeline_id}/share",
        json={"version_number": 1, "permission": "clone"},
    )
    token = share_res.json()["token"]

    client.delete(f"/api/pipelines/{pipeline_id}")

    lookup_res = client.get(f"/api/share/{token}")
    assert lookup_res.status_code == 404
    assert lookup_res.json()["detail"] == "Invalid or expired share link"

    clone_res = client.post(f"/api/share/{token}/clone", json={"name": "Should Fail"})
    assert clone_res.status_code == 404
    assert clone_res.json()["detail"] == "Invalid or expired share link"


def test_token_hash_stored_not_raw(client, db_session):
    res = client.post(
        "/api/pipelines/",
        json={"name": "Hashed Token", "workspace_json": {}, "pipeline_json": {}, "change_note": "v1"},
    )
    pipeline_id = res.json()["pipeline_id"]

    share_res = client.post(
        f"/api/pipelines/{pipeline_id}/share",
        json={"version_number": 1, "permission": "view"},
    )
    raw_token = share_res.json()["token"]

    shares = db_session.exec(select(PipelineShare)).all()
    assert len(shares) == 1
    assert shares[0].token_hash != raw_token
    assert len(shares[0].token_hash) == 64  # SHA-256 hex digest


def test_pipelines_not_rate_limited(client):
    for _ in range(40):
        res = client.get("/api/pipelines/")
        assert res.status_code == 200


def test_rate_limiting_applies_to_clone_post(client):
    blocked = False
    for _ in range(35):
        res = client.post("/api/share/dummy-token/clone", json={})
        if res.status_code == 429:
            blocked = True
            assert res.json()["detail"] == "Too many requests. Please try again later."
            break
    assert blocked, "Rate limiter did not block clone POST after 30 hits"


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


def test_edit_share_creates_version_in_original_pipeline(client):
    res = client.post(
        "/api/pipelines/",
        json={
            "name": "Collaborative Pipeline",
            "workspace_json": {"version": 1},
            "pipeline_json": {"steps": []},
        },
    )
    pipeline_id = res.json()["pipeline_id"]

    share_res = client.post(
        f"/api/pipelines/{pipeline_id}/share",
        json={"version_number": 1, "permission": "edit"},
    )
    assert share_res.status_code == 201
    token = share_res.json()["token"]

    lookup_res = client.get(f"/api/share/{token}")
    assert lookup_res.status_code == 200
    assert lookup_res.json()["permission"] == "edit"

    edit_res = client.post(
        f"/api/share/{token}/versions",
        json={
            "workspace_json": {"version": 2},
            "pipeline_json": {"steps": ["blur"]},
            "change_note": "Shared edit",
        },
    )
    assert edit_res.status_code == 201
    edited = edit_res.json()
    assert edited["pipeline_id"] == pipeline_id
    assert edited["version_number"] == 2

    pipelines = client.get("/api/pipelines/").json()
    assert len(pipelines) == 1
    versions = client.get(f"/api/pipelines/{pipeline_id}/versions").json()
    assert [version["version_number"] for version in versions] == [2, 1]


def test_only_edit_share_can_create_shared_version(client):
    res = client.post(
        "/api/pipelines/",
        json={"name": "Protected", "workspace_json": {}, "pipeline_json": {}},
    )
    pipeline_id = res.json()["pipeline_id"]
    payload = {"workspace_json": {"changed": True}, "pipeline_json": {}}

    for permission in ("view", "clone"):
        share_res = client.post(
            f"/api/pipelines/{pipeline_id}/share",
            json={"version_number": 1, "permission": permission},
        )
        token = share_res.json()["token"]
        edit_res = client.post(f"/api/share/{token}/versions", json=payload)
        assert edit_res.status_code == 403
        assert edit_res.json()["detail"] == "Editing not permitted for this share link"


def test_expired_edit_share_cannot_create_version(client):
    res = client.post(
        "/api/pipelines/",
        json={"name": "Expired Edit", "workspace_json": {}, "pipeline_json": {}},
    )
    pipeline_id = res.json()["pipeline_id"]
    expired_at = datetime.now(UTC) - timedelta(minutes=1)
    share_res = client.post(
        f"/api/pipelines/{pipeline_id}/share",
        json={
            "version_number": 1,
            "permission": "edit",
            "expires_at": expired_at.isoformat(),
        },
    )
    token = share_res.json()["token"]

    edit_res = client.post(
        f"/api/share/{token}/versions",
        json={"workspace_json": {}, "pipeline_json": {}},
    )
    assert edit_res.status_code == 404
    assert edit_res.json()["detail"] == "Invalid or expired share link"


def test_invalid_share_permission_is_rejected(client):
    res = client.post(
        "/api/pipelines/",
        json={"name": "Permission Validation", "workspace_json": {}, "pipeline_json": {}},
    )
    pipeline_id = res.json()["pipeline_id"]
    share_res = client.post(
        f"/api/pipelines/{pipeline_id}/share",
        json={"version_number": 1, "permission": "admin"},
    )
    assert share_res.status_code == 422


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

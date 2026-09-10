import hashlib
import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models.persistence import Pipeline, PipelineVersion
from app.models.pipeline import PipelineRequest, PipelineStep
from app.services.pipeline_executor import execute_pipeline
from app.utils.image import decode_base64_image


def test_full_pipeline_lifecycle(client: TestClient, session: Session, sample_image_b64: str):
    """Lifecycle test: REST API pipeline creation -> SQLModel storage -> JSON retrieval -> PipelineExecutor
    execution checksum verification."""
    # 1. REST API pipeline creation (creates Pipeline record + v1 PipelineVersion)
    pipeline_payload = {
        "name": "Integration Test Pipeline",
        "owner_id": "test_user_1",
        "workspace_json": {
            "blocks": [
                {"id": "step_1", "type": "imageconvertions_grayimage"},
                {"id": "step_2", "type": "filtering_cannyedge"},
            ]
        },
        "pipeline_json": {
            "nodes": [
                {"id": "step_1", "type": "imageconvertions_grayimage"},
                {"id": "step_2", "type": "filtering_cannyedge"},
            ],
            "edges": [{"from": "step_1", "to": "step_2"}],
        },
        "change_note": "Initial Integration v1",
    }
    create_res = client.post("/api/pipelines/", json=pipeline_payload)
    assert create_res.status_code == 201, create_res.text
    created_data = create_res.json()
    pipeline_id = created_data["pipeline_id"]
    assert created_data["version_number"] == 1
    assert created_data["change_note"] == "Initial Integration v1"

    # 2. SQLModel DB storage verification
    db_pipeline = session.get(Pipeline, uuid.UUID(pipeline_id))
    assert db_pipeline is not None
    assert db_pipeline.name == "Integration Test Pipeline"
    assert db_pipeline.owner_id == "test_user_1"

    db_versions = session.exec(
        select(PipelineVersion).where(PipelineVersion.pipeline_id == uuid.UUID(pipeline_id))
    ).all()
    assert len(db_versions) == 1
    assert db_versions[0].version_number == 1
    assert db_versions[0].pipeline_json == pipeline_payload["pipeline_json"]

    # 3. JSON retrieval via REST API
    get_res = client.get(f"/api/pipelines/{pipeline_id}")
    assert get_res.status_code == 200
    retrieved_version = get_res.json()
    assert retrieved_version["pipeline_id"] == pipeline_id
    assert retrieved_version["version_number"] == 1
    retrieved_json = retrieved_version["pipeline_json"]

    # Extract pipeline steps from retrieved JSON
    nodes = retrieved_json.get("nodes", [])
    steps = [PipelineStep(block_id=n["id"], type=n["type"]) for n in nodes]

    # 4. PipelineExecutor execution & checksum verification
    exec_req = PipelineRequest(image=sample_image_b64, image_format="png", pipeline=steps)
    exec_resp = execute_pipeline(exec_req)

    assert exec_resp.success is True
    assert exec_resp.image is not None
    assert len(exec_resp.step_results) == 2

    # Verify checksum of execution output image
    result_img = decode_base64_image(exec_resp.image)
    checksum = hashlib.sha256(result_img.tobytes()).hexdigest()
    assert len(checksum) == 64

    # Re-running same deterministic pipeline on same input yields identical checksum
    exec_resp2 = execute_pipeline(exec_req)
    result_img2 = decode_base64_image(exec_resp2.image)
    checksum2 = hashlib.sha256(result_img2.tobytes()).hexdigest()
    assert checksum == checksum2


def test_share_token_access_control(client: TestClient):
    """Test public share link generation and permission enforcement ('view' vs 'edit')."""
    # Create base pipeline
    create_res = client.post(
        "/api/pipelines/",
        json={
            "name": "Access Control Test",
            "workspace_json": {"version": 1},
            "pipeline_json": {"nodes": []},
            "change_note": "v1",
        },
    )
    assert create_res.status_code == 201
    pipeline_id = create_res.json()["pipeline_id"]

    # 1. Generate 'view' permission share link
    view_share_res = client.post(
        f"/api/pipelines/{pipeline_id}/share",
        json={"version_number": 1, "permission": "view"},
    )
    assert view_share_res.status_code == 201
    view_token = view_share_res.json()["token"]

    # Lookup 'view' share link
    lookup_view = client.get(f"/api/share/{view_token}")
    assert lookup_view.status_code == 200
    assert lookup_view.json()["permission"] == "view"
    assert lookup_view.json()["pipeline_name"] == "Access Control Test"

    # Attempt edit version push with 'view' share link -> HTTP 403 Forbidden
    attempt_edit_view = client.post(
        f"/api/share/{view_token}/versions",
        json={
            "workspace_json": {"version": 2},
            "pipeline_json": {"nodes": [{"id": "n1", "type": "imageconvertions_grayimage"}]},
            "change_note": "Unauthorized Edit Attempt",
        },
    )
    assert attempt_edit_view.status_code == 403
    assert attempt_edit_view.json()["detail"] == "Editing not permitted for this share link"

    # 2. Generate 'edit' permission share link
    edit_share_res = client.post(
        f"/api/pipelines/{pipeline_id}/share",
        json={"version_number": 1, "permission": "edit"},
    )
    assert edit_share_res.status_code == 201
    edit_token = edit_share_res.json()["token"]

    # Lookup 'edit' share link
    lookup_edit = client.get(f"/api/share/{edit_token}")
    assert lookup_edit.status_code == 200
    assert lookup_edit.json()["permission"] == "edit"

    # Save new version via 'edit' share link -> HTTP 201 Created
    push_edit_res = client.post(
        f"/api/share/{edit_token}/versions",
        json={
            "workspace_json": {"version": 2},
            "pipeline_json": {"nodes": [{"id": "n1", "type": "imageconvertions_grayimage"}]},
            "change_note": "Authorized Shared Edit",
        },
    )
    assert push_edit_res.status_code == 201
    new_version_data = push_edit_res.json()
    assert new_version_data["version_number"] == 2
    assert new_version_data["pipeline_id"] == pipeline_id

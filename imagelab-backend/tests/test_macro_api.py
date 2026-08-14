import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.database import get_db
from app.main import app
from app.models.persistence import Pipeline, PipelineVersion

# In-memory SQLite DB for testing
test_db_url = "sqlite://"
test_engine = create_engine(
    test_db_url,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@pytest.fixture(name="session")
def db_session_fixture():
    SQLModel.metadata.create_all(test_engine)
    with Session(test_engine) as session:
        yield session
    SQLModel.metadata.drop_all(test_engine)


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_db_override():
        return session

    app.dependency_overrides[get_db] = get_db_override
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


def test_macro_crud_lifecycle(client: TestClient):
    # 1. Create a Macro
    macro_graph = {
        "nodes": [
            {"id": "in_1", "type": "macro_input"},
            {"id": "blur_1", "type": "blurring_applyblur", "params": {"kernelSize": 5}},
            {"id": "out_1", "type": "macro_output"},
        ],
        "edges": [
            {"from": "in_1", "to": "blur_1"},
            {"from": "blur_1", "to": "out_1"},
        ],
    }
    create_payload = {
        "name": "Custom Blur Macro",
        "description": "Applies a standard 5x5 blur",
        "workspace_json": {"blocks": []},
        "pipeline_json": macro_graph,
    }

    response = client.post("/api/v1/macros", json=create_payload)
    assert response.status_code == 201, response.text
    data = response.json()
    macro_id = data["macro_id"]
    assert data["name"] == "Custom Blur Macro"
    assert data["version_number"] == 1

    # 2. List Macros
    response = client.get("/api/v1/macros")
    assert response.status_code == 200
    macros = response.json()
    created_macro = next((m for m in macros if m.get("id") == macro_id or m.get("macro_id") == macro_id), None)

    assert created_macro is not None, f"Macro with ID {macro_id} not found in response list: {macros}"
    assert created_macro["name"] == "Custom Blur Macro"
    # 3. Retrieve Macro details
    response = client.get(f"/api/v1/macros/{macro_id}")
    assert response.status_code == 200
    detail = response.json()
    assert detail["macro_id"] == macro_id
    assert detail["pipeline_json"] == macro_graph

    # 4. Update Macro
    updated_graph = {
        "nodes": [
            {"id": "in_1", "type": "macro_input"},
            {"id": "blur_1", "type": "blurring_applyblur", "params": {"kernelSize": 9}},
            {"id": "out_1", "type": "macro_output"},
        ],
        "edges": [
            {"from": "in_1", "to": "blur_1"},
            {"from": "blur_1", "to": "out_1"},
        ],
    }
    update_payload = {
        "name": "Updated Blur Macro",
        "pipeline_json": updated_graph,
        "description": "Updated kernel size to 9",
    }
    response = client.put(f"/api/v1/macros/{macro_id}", json=update_payload)
    assert response.status_code == 200
    updated_data = response.json()
    assert updated_data["name"] == "Updated Blur Macro"
    assert updated_data["version_number"] == 2
    assert updated_data["pipeline_json"]["nodes"][1]["params"]["kernelSize"] == 9

    # 5. Delete Macro
    response = client.delete(f"/api/v1/macros/{macro_id}")
    assert response.status_code == 204

    # Verify deleted
    response = client.get(f"/api/v1/macros/{macro_id}")
    assert response.status_code == 404


def test_macro_graph_validation_rejects_cycles(client: TestClient):
    # Cyclic macro graph
    cyclic_graph = {
        "nodes": [
            {"id": "node_a", "type": "blurring_applyblur"},
            {"id": "node_b", "type": "filtering_cannyedge"},
        ],
        "edges": [
            {"from": "node_a", "to": "node_b"},
            {"from": "node_b", "to": "node_a"},
        ],
    }
    create_payload = {
        "name": "Cyclic Macro",
        "pipeline_json": cyclic_graph,
    }

    response = client.post("/api/v1/macros", json=create_payload)
    assert response.status_code == 400
    assert "cycle detected" in response.json()["detail"].lower()


def test_macro_dependency_safety_check_blocks_deletion(client: TestClient, session: Session):
    # 1. Create Macro M1
    macro_graph = {
        "nodes": [
            {"id": "in_1", "type": "macro_input"},
            {"id": "gray_1", "type": "imageconvertions_grayimage"},
            {"id": "out_1", "type": "macro_output"},
        ],
        "edges": [{"from": "in_1", "to": "gray_1"}, {"from": "gray_1", "to": "out_1"}],
    }
    res = client.post("/api/v1/macros", json={"name": "Grayscale Macro", "pipeline_json": macro_graph})
    assert res.status_code == 201
    macro_id = res.json()["macro_id"]

    # 2. Create a Pipeline referencing Macro M1
    parent_pipeline = Pipeline(name="Parent Pipeline", is_macro=False)
    session.add(parent_pipeline)
    session.flush()

    parent_graph = {
        "nodes": [
            {"id": "read", "type": "basic_readimage"},
            {"id": "m1_ref", "type": "macro_ref", "params": {"macro_id": macro_id}},
        ],
        "edges": [{"from": "read", "to": "m1_ref"}],
    }
    session.add(PipelineVersion(pipeline_id=parent_pipeline.id, version_number=1, pipeline_json=parent_graph))
    session.commit()

    # 3. Attempt to delete Macro M1 -> Should be blocked (409 Conflict)
    del_res = client.delete(f"/api/v1/macros/{macro_id}")
    assert del_res.status_code == 409
    assert "referenced by active pipelines" in del_res.json()["detail"]

    # 4. Remove parent pipeline from DB
    session.delete(parent_pipeline)
    session.commit()

    # 5. Attempt to delete Macro M1 again -> Should succeed (204 No Content)
    del_res2 = client.delete(f"/api/v1/macros/{macro_id}")
    assert del_res2.status_code == 204


def test_macro_expansion_and_step_inspection(client: TestClient, session: Session, sample_image_b64: str):
    # 1. Create Macro M1
    macro_graph = {
        "nodes": [
            {"id": "in_1", "type": "macro_input"},
            {"id": "gray_step", "type": "imageconvertions_grayimage"},
            {"id": "out_1", "type": "macro_output"},
        ],
        "edges": [{"from": "in_1", "to": "gray_step"}, {"from": "gray_step", "to": "out_1"}],
    }
    res = client.post("/api/v1/macros", json={"name": "Grayscale Macro", "pipeline_json": macro_graph})
    assert res.status_code == 201
    macro_id = res.json()["macro_id"]

    # 2. Create Parent Pipeline referencing Macro M1
    parent_pipeline = Pipeline(name="Parent Pipeline", is_macro=False)
    session.add(parent_pipeline)
    session.flush()

    parent_graph = {
        "nodes": [
            {"id": "read_step", "type": "basic_readimage"},
            {"id": "m1_node", "type": "macro_ref", "params": {"macro_id": macro_id}},
            {"id": "canny_step", "type": "filtering_cannyedge"},
        ],
        "edges": [
            {"from": "read_step", "to": "m1_node"},
            {"from": "m1_node", "to": "canny_step"},
        ],
    }
    session.add(PipelineVersion(pipeline_id=parent_pipeline.id, version_number=1, pipeline_json=parent_graph))
    session.commit()

    # 3. Execute parent graph pipeline
    from app.models.pipeline import PipelineRequest
    from app.services.graph_engine import execute_graph_pipeline

    req = PipelineRequest(image=sample_image_b64, pipeline=[])
    exec_res = execute_graph_pipeline(session, parent_pipeline.id, req)

    assert exec_res.success
    assert exec_res.execution_id is not None
    # Filtered execution steps: m1_node:gray_step, canny_step
    block_ids = [r.block_id for r in exec_res.step_results]
    assert "m1_node:gray_step" in block_ids
    assert "canny_step" in block_ids

    # 4. Inspect macro step via parent block_id "m1_node"
    inspect_res = client.get(
        f"/api/v1/pipeline/executions/{exec_res.execution_id}/steps/inspect",
        params={"block_id": "m1_node"},
    )
    assert inspect_res.status_code == 200
    inspect_data = inspect_res.json()
    assert inspect_data["success"]
    assert inspect_data["type"] == "imageconvertions_grayimage"


def test_control_flow_macro_pipeline_execution(client: TestClient, sample_image_b64: str):
    execute_payload = {
        "image": sample_image_b64,
        "image_format": "png",
        "pipeline": [
            {
                "type": "macro_blend",
                "block_id": "blend_node",
                "params": {
                    "alpha": 0.5,
                    "op1_branch": [{"type": "imageconvertions_grayimage"}],
                    "op2_branch": [{"type": "blurring_applyblur", "params": {"widthSize": 5, "heightSize": 5}}],
                },
            },
            {
                "type": "macro_if_else",
                "block_id": "if_else_node",
                "params": {
                    "metric": "mean_brightness",
                    "comparator": ">",
                    "threshold": 10.0,
                    "if_branch": [{"type": "imageconvertions_grayimage"}],
                    "else_branch": [],
                },
            },
        ],
    }

    res = client.post("/api/v1/pipeline/executions", json=execute_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["image"] is not None

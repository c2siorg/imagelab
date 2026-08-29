import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.exceptions import MacroDepthLimitExceeded
from app.models.persistence import Pipeline, PipelineVersion
from app.services.graph_engine import prepare_pipeline


def test_nested_macro_expansion(client: TestClient, session: Session, sample_image_b64: str):
    """Test multi-level subgraph macro expansion (Macro A -> Macro B -> Macro C)."""
    # 1. Create Macro C (innermost: grayscale)
    c_graph = {
        "nodes": [
            {"id": "c_in", "type": "macro_input"},
            {"id": "c_gray", "type": "imageconvertions_grayimage"},
            {"id": "c_out", "type": "macro_output"},
        ],
        "edges": [
            {"from": "c_in", "to": "c_gray"},
            {"from": "c_gray", "to": "c_out"},
        ],
    }
    res_c = client.post("/api/v1/macros", json={"name": "Macro C", "pipeline_json": c_graph})
    assert res_c.status_code == 201
    macro_c_id = res_c.json()["macro_id"]

    # 2. Create Macro B (references Macro C)
    b_graph = {
        "nodes": [
            {"id": "b_in", "type": "macro_input"},
            {"id": "b_ref_c", "type": "macro_ref", "params": {"macro_id": macro_c_id}},
            {"id": "b_out", "type": "macro_output"},
        ],
        "edges": [
            {"from": "b_in", "to": "b_ref_c"},
            {"from": "b_ref_c", "to": "b_out"},
        ],
    }
    res_b = client.post("/api/v1/macros", json={"name": "Macro B", "pipeline_json": b_graph})
    assert res_b.status_code == 201
    macro_b_id = res_b.json()["macro_id"]

    # 3. Create Macro A (references Macro B)
    a_graph = {
        "nodes": [
            {"id": "a_in", "type": "macro_input"},
            {"id": "a_ref_b", "type": "macro_ref", "params": {"macro_id": macro_b_id}},
            {"id": "a_out", "type": "macro_output"},
        ],
        "edges": [
            {"from": "a_in", "to": "a_ref_b"},
            {"from": "a_ref_b", "to": "a_out"},
        ],
    }
    res_a = client.post("/api/v1/macros", json={"name": "Macro A", "pipeline_json": a_graph})
    assert res_a.status_code == 201
    macro_a_id = res_a.json()["macro_id"]

    # 4. Create Parent Pipeline referencing Macro A
    parent = Pipeline(name="Root Pipeline", is_macro=False)
    session.add(parent)
    session.flush()

    root_graph = {
        "nodes": [
            {"id": "root_read", "type": "basic_readimage"},
            {"id": "root_ref_a", "type": "macro_ref", "params": {"macro_id": macro_a_id}},
            {"id": "root_canny", "type": "filtering_cannyedge"},
        ],
        "edges": [
            {"from": "root_read", "to": "root_ref_a"},
            {"from": "root_ref_a", "to": "root_canny"},
        ],
    }
    session.add(PipelineVersion(pipeline_id=parent.id, version_number=1, pipeline_json=root_graph))
    session.commit()

    # 5. Compile / Prepare pipeline and verify deep expansion
    steps = prepare_pipeline(session, parent.id, input_channels=3)
    block_ids = [s.block_id for s in steps]

    # Verify namespaced inner node from Macro C is present in compiled step sequence
    assert "root_ref_a:a_ref_b:b_ref_c:c_gray" in block_ids
    assert "root_canny" in block_ids


def test_macro_max_depth_exceeded_error(client: TestClient, session: Session):
    """Verify MacroDepthLimitExceeded is raised when macro nesting depth exceeds 10."""
    macro_ids = []

    # Create a chain of 11 macros (Macro 0 -> Macro 1 -> ... -> Macro 10)
    for i in range(11):
        if i == 0:
            # Leaf macro (depth 1)
            graph = {
                "nodes": [
                    {"id": f"in_{i}", "type": "macro_input"},
                    {"id": f"step_{i}", "type": "imageconvertions_grayimage"},
                    {"id": f"out_{i}", "type": "macro_output"},
                ],
                "edges": [{"from": f"in_{i}", "to": f"step_{i}"}, {"from": f"step_{i}", "to": f"out_{i}"}],
            }
        else:
            # References previous macro
            prev_id = macro_ids[-1]
            graph = {
                "nodes": [
                    {"id": f"in_{i}", "type": "macro_input"},
                    {"id": f"ref_{i}", "type": "macro_ref", "params": {"macro_id": prev_id}},
                    {"id": f"out_{i}", "type": "macro_output"},
                ],
                "edges": [{"from": f"in_{i}", "to": f"ref_{i}"}, {"from": f"ref_{i}", "to": f"out_{i}"}],
            }
        res = client.post("/api/v1/macros", json={"name": f"Macro {i}", "pipeline_json": graph})
        assert res.status_code == 201
        macro_ids.append(res.json()["macro_id"])

    # Create root pipeline referencing the top of the 11-level macro chain
    top_macro_id = macro_ids[-1]
    parent = Pipeline(name="Deep Root Pipeline", is_macro=False)
    session.add(parent)
    session.flush()

    root_graph = {
        "nodes": [
            {"id": "read", "type": "basic_readimage"},
            {"id": "top_ref", "type": "macro_ref", "params": {"macro_id": top_macro_id}},
        ],
        "edges": [{"from": "read", "to": "top_ref"}],
    }
    session.add(PipelineVersion(pipeline_id=parent.id, version_number=1, pipeline_json=root_graph))
    session.commit()

    # Expanding 11 deep macro chain should raise MacroDepthLimitExceeded
    with pytest.raises(MacroDepthLimitExceeded) as exc_info:
        prepare_pipeline(session, parent.id, input_channels=3)

    assert "exceeded" in str(exc_info.value).lower() or "depth" in str(exc_info.value).lower()

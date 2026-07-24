import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.models.graph import GraphCycleError
from app.models.persistence import Pipeline, PipelineVersion
from app.models.pipeline import PipelineRequest
from app.services.graph_engine import GraphTypeError, execute_graph_pipeline, prepare_pipeline

# Create in-memory SQLite engine for persistence testing
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


def test_linear_pipeline_regression(session, sample_image_b64):
    # 1. Create a simple linear pipeline in the DB
    pipeline = Pipeline(name="Linear Regression Pipeline")
    session.add(pipeline)
    session.flush()

    graph_json = {
        "nodes": [
            {"id": "read_node", "type": "basic_readimage"},
            {"id": "blur_node", "type": "blurring_applyblur", "params": {"kernelSize": 5}},
        ],
        "edges": [{"from": "read_node", "to": "blur_node"}],
    }

    version = PipelineVersion(
        pipeline_id=pipeline.id,
        version_number=1,
        workspace_json={},
        pipeline_json=graph_json,
    )
    session.add(version)
    session.commit()

    # 2. Run execute_graph_pipeline
    req = PipelineRequest(image=sample_image_b64, pipeline=[])
    res = execute_graph_pipeline(session, pipeline.id, req)

    # 3. Assert success and correctness of results
    assert res.success
    assert len(res.step_results) == 1  # basic_readimage is NOOP_TYPES so it is skipped during execution
    assert res.step_results[0].block_id == "blur_node"
    assert res.step_results[0].success


def test_two_level_nested_macro_expansion(session):
    # Setup 2-level macro: Parent -> Macro A -> Macro B

    # 1. Create Macro B (converts to grayscale)
    macro_b = Pipeline(name="Macro B")
    session.add(macro_b)
    session.flush()

    macro_b_graph = {
        "nodes": [
            {"id": "in_b", "type": "macro_input"},
            {"id": "gray", "type": "imageconvertions_grayimage"},
            {"id": "out_b", "type": "macro_output"},
        ],
        "edges": [{"from": "in_b", "to": "gray"}, {"from": "gray", "to": "out_b"}],
    }

    session.add(PipelineVersion(pipeline_id=macro_b.id, version_number=1, pipeline_json=macro_b_graph))

    # 2. Create Macro A (references Macro B)
    macro_a = Pipeline(name="Macro A")
    session.add(macro_a)
    session.flush()

    macro_a_graph = {
        "nodes": [
            {"id": "in_a", "type": "macro_input"},
            {"id": "m_b", "type": "macro_ref", "params": {"macro_id": str(macro_b.id)}},
            {"id": "out_a", "type": "macro_output"},
        ],
        "edges": [{"from": "in_a", "to": "m_b"}, {"from": "m_b", "to": "out_a"}],
    }

    session.add(PipelineVersion(pipeline_id=macro_a.id, version_number=1, pipeline_json=macro_a_graph))

    # 3. Create Parent Pipeline (references Macro A)
    parent = Pipeline(name="Parent Pipeline")
    session.add(parent)
    session.flush()

    parent_graph = {
        "nodes": [
            {"id": "read", "type": "basic_readimage"},
            {"id": "m_a", "type": "macro_ref", "params": {"macro_id": str(macro_a.id)}},
            {"id": "canny", "type": "filtering_cannyedge"},
        ],
        "edges": [{"from": "read", "to": "m_a"}, {"from": "m_a", "to": "canny"}],
    }

    session.add(PipelineVersion(pipeline_id=parent.id, version_number=1, pipeline_json=parent_graph))
    session.commit()

    # 4. Compile the parent pipeline using prepare_pipeline (3 channels input)
    steps = prepare_pipeline(session, parent.id, 3)

    # 5. Assert correctly expanded list of steps (ignoring macro_input/macro_output nodes)
    # Expected nodes in expanded graph: read, m_a:in_a, m_a:m_b:in_b, m_a:m_b:gray, m_a:m_b:out_b, m_a:out_a, canny
    # After filtering portal nodes, remaining execution steps: read, m_a:m_b:gray, canny
    # basic_readimage is kept in compiled steps (it is skipped during final CV2 execution, but is a compiled step)
    step_ids = [step.block_id for step in steps]
    assert step_ids == ["read", "m_a:m_b:gray", "canny"]

    # Verify that the operators are preserved
    assert steps[0].type == "basic_readimage"
    assert steps[1].type == "imageconvertions_grayimage"
    assert steps[2].type == "filtering_cannyedge"


def test_cyclic_macro_nesting_fails(session):
    # Macro A references B, Macro B references A -> Infinite cyclic nesting

    macro_b = Pipeline(name="Macro B")
    session.add(macro_b)
    session.flush()

    macro_a = Pipeline(name="Macro A")
    session.add(macro_a)
    session.flush()

    # Macro B graph (references A)
    macro_b_graph = {
        "nodes": [
            {"id": "in_b", "type": "macro_input"},
            {"id": "m_a", "type": "macro_ref", "params": {"macro_id": str(macro_a.id)}},
            {"id": "out_b", "type": "macro_output"},
        ],
        "edges": [{"from": "in_b", "to": "m_a"}, {"from": "m_a", "to": "out_b"}],
    }
    session.add(PipelineVersion(pipeline_id=macro_b.id, version_number=1, pipeline_json=macro_b_graph))

    # Macro A graph (references B)
    macro_a_graph = {
        "nodes": [
            {"id": "in_a", "type": "macro_input"},
            {"id": "m_b", "type": "macro_ref", "params": {"macro_id": str(macro_b.id)}},
            {"id": "out_a", "type": "macro_output"},
        ],
        "edges": [{"from": "in_a", "to": "m_b"}, {"from": "m_b", "to": "out_a"}],
    }
    session.add(PipelineVersion(pipeline_id=macro_a.id, version_number=1, pipeline_json=macro_a_graph))

    # Parent pipeline references A
    parent = Pipeline(name="Parent Pipeline")
    session.add(parent)
    session.flush()

    parent_graph = {
        "nodes": [
            {"id": "read", "type": "basic_readimage"},
            {"id": "m_a", "type": "macro_ref", "params": {"macro_id": str(macro_a.id)}},
        ],
        "edges": [{"from": "read", "to": "m_a"}],
    }
    session.add(PipelineVersion(pipeline_id=parent.id, version_number=1, pipeline_json=parent_graph))
    session.commit()

    # Verify cyclic macro reference raises GraphCycleError containing the cyclic nesting path
    with pytest.raises(GraphCycleError) as excinfo:
        prepare_pipeline(session, parent.id, 3)

    assert excinfo.value.cycle == [str(macro_a.id), str(macro_b.id), str(macro_a.id)]


def test_type_integrity_channel_mismatch(session):
    # Setup a graph where a grayscale image feeds directly into an input that strictly requires 3/4 channels.
    # imageconvertions_colortobinary expects 3 or 4 channels.
    # We feed it the output of imageconvertions_grayimage (1 channel).

    pipeline = Pipeline(name="Type Mismatch Pipeline")
    session.add(pipeline)
    session.flush()

    # Invalid graph
    invalid_graph = {
        "nodes": [
            {"id": "read", "type": "basic_readimage"},
            {"id": "gray", "type": "imageconvertions_grayimage"},
            {"id": "color_to_bin", "type": "imageconvertions_colortobinary"},
        ],
        "edges": [{"from": "read", "to": "gray"}, {"from": "gray", "to": "color_to_bin"}],
    }

    session.add(PipelineVersion(pipeline_id=pipeline.id, version_number=1, pipeline_json=invalid_graph))
    session.commit()

    # Compiling this pipeline with 3-channel input should raise GraphTypeError
    with pytest.raises(GraphTypeError) as excinfo:
        prepare_pipeline(session, pipeline.id, 3)

    assert "Type mismatch on node 'color_to_bin'" in str(excinfo.value)
    assert "expected channels in [3, 4], got 1 channels" in str(excinfo.value)


def test_type_integrity_multi_port_compatible_and_incompatible(session):
    # Setup custom merge node (expects "image": [3,4], "mask": [1])
    # Case A: Valid connection:
    #   read (3 channels) -> merge (port="image")
    #   read (3 channels) -> gray (1 channel) -> merge (port="mask")

    pipeline = Pipeline(name="Multi Port Pipeline")
    session.add(pipeline)
    session.flush()

    valid_graph = {
        "nodes": [
            {"id": "read", "type": "basic_readimage"},
            {"id": "gray", "type": "imageconvertions_grayimage"},
            {"id": "merge", "type": "merge_images"},
        ],
        "edges": [
            {"from": "read", "to": "merge", "input_port": "image"},
            {"from": "gray", "to": "merge", "input_port": "mask"},
        ],
    }

    session.add(PipelineVersion(pipeline_id=pipeline.id, version_number=1, pipeline_json=valid_graph))
    session.commit()

    # Should prepare without error since types match
    steps = prepare_pipeline(session, pipeline.id, 3)
    assert len(steps) == 3

    # Case B: Incompatible connection:
    #   read (3 channels) -> merge (port="mask")  -- invalid (expects 1 channel)
    #   gray (1 channel) -> merge (port="image")  -- invalid (expects 3/4 channels)
    pipeline_invalid = Pipeline(name="Incompatible Multi Port Pipeline")
    session.add(pipeline_invalid)
    session.flush()

    invalid_graph = {
        "nodes": [
            {"id": "read", "type": "basic_readimage"},
            {"id": "gray", "type": "imageconvertions_grayimage"},
            {"id": "merge", "type": "merge_images"},
        ],
        "edges": [
            {"from": "read", "to": "merge", "input_port": "mask"},
            {"from": "gray", "to": "merge", "input_port": "image"},
        ],
    }

    session.add(PipelineVersion(pipeline_id=pipeline_invalid.id, version_number=1, pipeline_json=invalid_graph))
    session.commit()

    with pytest.raises(GraphTypeError) as excinfo:
        prepare_pipeline(session, pipeline_invalid.id, 3)

    assert "Type mismatch on node 'merge'" in str(excinfo.value)

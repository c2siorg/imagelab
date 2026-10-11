from app.models.persistence import Pipeline, PipelineVersion
from app.models.pipeline import PipelineRequest, PipelineStep
from app.operators.registry import (
    LEGACY_OPERATOR_ALIASES,
    OPERATOR_REGISTRY,
    get_operator,
    resolve_operator_name,
)
from app.services.graph_engine import execute_graph_pipeline, prepare_pipeline
from app.services.pipeline_executor import execute_pipeline


def test_legacy_operator_aliases_mapping():
    """Verify all 15 conversion operators are covered in the legacy alias table."""
    assert len(LEGACY_OPERATOR_ALIASES) == 15
    for legacy_key, canonical_key in LEGACY_OPERATOR_ALIASES.items():
        assert legacy_key.startswith("imageconvertions_")
        assert canonical_key.startswith("imageconversions_")
        assert canonical_key in OPERATOR_REGISTRY
        assert get_operator(legacy_key) is not None
        assert get_operator(legacy_key) is OPERATOR_REGISTRY[canonical_key]


def test_resolve_operator_name():
    """Verify resolve_operator_name resolves legacy keys and passes non-legacy keys through."""
    assert resolve_operator_name("imageconvertions_grayimage") == "imageconversions_grayimage"
    assert resolve_operator_name("imageconversions_grayimage") == "imageconversions_grayimage"
    assert resolve_operator_name("basic_readimage") == "basic_readimage"


def test_legacy_pipeline_step_executes(sample_image_b64: str):
    """Regression test: Pipeline containing legacy 'imageconvertions_*' executes successfully."""
    request = PipelineRequest(
        image=sample_image_b64,
        image_format="png",
        pipeline=[PipelineStep(block_id="legacy-gray", type="imageconvertions_grayimage", params={})],
    )
    result = execute_pipeline(request)
    assert result.success is True
    assert result.image is not None
    assert len(result.step_results) == 1
    assert result.step_results[0].success is True


def test_legacy_stored_pipeline_executes(session, sample_image_b64: str):
    """Regression test: Stored pipeline version with legacy 'imageconvertions_*' nodes executes end-to-end."""
    pipeline = Pipeline(name="Legacy Saved Conversions Pipeline")
    session.add(pipeline)
    session.flush()

    legacy_graph = {
        "nodes": [
            {"id": "read", "type": "basic_readimage"},
            {"id": "legacy_gray", "type": "imageconvertions_grayimage"},
            {"id": "legacy_invert", "type": "imageconvertions_invertimage"},
        ],
        "edges": [
            {"from": "read", "to": "legacy_gray"},
            {"from": "legacy_gray", "to": "legacy_invert"},
        ],
    }

    session.add(PipelineVersion(pipeline_id=pipeline.id, version_number=1, pipeline_json=legacy_graph))
    session.commit()

    steps = prepare_pipeline(session, pipeline.id, 3)
    assert len(steps) == 3
    assert steps[1].type == "imageconversions_grayimage"
    assert steps[2].type == "imageconversions_invertimage"

    request = PipelineRequest(image=sample_image_b64, image_format="png", pipeline=[])
    response = execute_graph_pipeline(session, pipeline.id, request)
    assert response.success is True
    assert response.image is not None
    assert len(response.step_results) == 2

import numpy as np
from fastapi.testclient import TestClient

from app.models.pipeline import PipelineRequest, PipelineStep
from app.services.pipeline_executor import (
    MAX_EXECUTION_CACHE_ENTRIES,
    execute_pipeline,
    inspect_step,
)
from app.utils.image import decode_base64_image, encode_image_base64


def test_low_res_preview_generation():
    """Verify that execution step outputs generate 128px downscaled thumbnail previews."""
    # Create a high-res test image (640x480)
    large_img = np.zeros((480, 640, 3), dtype=np.uint8)
    large_img[:] = (120, 180, 240)
    large_b64 = encode_image_base64(large_img, "png")

    req = PipelineRequest(
        image=large_b64,
        image_format="png",
        pipeline=[
            PipelineStep(block_id="step_gray", type="imageconvertions_grayimage"),
            PipelineStep(block_id="step_blur", type="blurring_applyblur", params={"kernelSize": 5}),
        ],
    )
    resp = execute_pipeline(req)

    assert resp.success is True
    assert len(resp.step_results) == 2

    for result in resp.step_results:
        assert result.thumbnail is not None
        # Decode thumbnail base64 and verify dimensions do not exceed 128px on longest side
        thumb_img = decode_base64_image(result.thumbnail)
        h, w = thumb_img.shape[:2]
        assert max(h, w) <= 128


def test_high_res_inspection_on_demand(client: TestClient):
    """Verify full-resolution step buffer retrieval on-demand via inspect_step endpoint."""
    # Create test image (300x400)
    orig_img = np.full((300, 400, 3), 200, dtype=np.uint8)
    orig_b64 = encode_image_base64(orig_img, "png")

    execute_payload = {
        "image": orig_b64,
        "image_format": "png",
        "pipeline": [
            {
                "block_id": "step_gray_node",
                "type": "imageconvertions_grayimage",
                "params": {},
            }
        ],
    }

    exec_res = client.post("/api/v1/pipeline/executions", json=execute_payload)
    assert exec_res.status_code == 200
    exec_data = exec_res.json()
    assert exec_data["success"] is True
    execution_id = exec_data["execution_id"]
    assert execution_id is not None

    # Fetch high-res inspection buffer on demand for step_gray_node
    inspect_res = client.get(
        f"/api/v1/pipeline/executions/{execution_id}/steps/inspect",
        params={"block_id": "step_gray_node"},
    )
    assert inspect_res.status_code == 200
    inspect_data = inspect_res.json()
    assert inspect_data["success"] is True
    assert inspect_data["block_id"] == "step_gray_node"
    assert inspect_data["type"] == "imageconvertions_grayimage"
    assert inspect_data["image"] is not None

    # Decode high-res image and verify original dimensions are preserved (300x400)
    full_img = decode_base64_image(inspect_data["image"])
    assert full_img.shape[0] == 300
    assert full_img.shape[1] == 400
    # Also verify analysis stats and histogram are populated
    assert inspect_data["analysis"]["width"] == 400
    assert inspect_data["analysis"]["height"] == 300
    assert inspect_data["histogram"] is not None


def test_intermediate_buffer_eviction(sample_image_b64: str):
    """Verify LRU cache eviction when execution count exceeds MAX_EXECUTION_CACHE_ENTRIES."""
    req = PipelineRequest(
        image=sample_image_b64,
        image_format="png",
        pipeline=[PipelineStep(block_id="evict_step", type="imageconvertions_grayimage")],
    )

    execution_ids = []
    # Run MAX_EXECUTION_CACHE_ENTRIES + 5 executions
    total_executions = MAX_EXECUTION_CACHE_ENTRIES + 5
    for _ in range(total_executions):
        resp = execute_pipeline(req)
        assert resp.success is True
        execution_ids.append(resp.execution_id)

    # First 5 executions should have been LRU evicted
    for evicted_id in execution_ids[:5]:
        buf = inspect_step(evicted_id, "evict_step")
        assert buf is None

    # Last MAX_EXECUTION_CACHE_ENTRIES executions should remain available
    for active_id in execution_ids[5:]:
        buf = inspect_step(active_id, "evict_step")
        assert buf is not None
        assert buf["execution_id"] == active_id

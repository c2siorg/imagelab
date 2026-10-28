import cv2
import numpy as np
from fastapi.testclient import TestClient

from app.models.pipeline import PipelineRequest, PipelineStep
from app.services import pipeline_executor
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
            PipelineStep(block_id="step_gray", type="imageconversions_grayimage"),
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
                "type": "imageconversions_grayimage",
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
    assert inspect_data["type"] == "imageconversions_grayimage"
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
        pipeline=[PipelineStep(block_id="evict_step", type="imageconversions_grayimage")],
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


def test_cache_steps_disabled(sample_image_b64: str):
    """Verify that setting cache_steps=False skips execution caching and sets has_full_image=False."""
    pipeline_executor._EXECUTION_CACHE.clear()
    req = PipelineRequest(
        image=sample_image_b64,
        image_format="png",
        pipeline=[PipelineStep(block_id="step_1", type="imageconversions_grayimage")],
    )
    resp = execute_pipeline(req, cache_steps=False)
    assert resp.success is True
    assert len(resp.step_results) == 1
    assert resp.step_results[0].has_full_image is False
    assert pipeline_executor.inspect_step(resp.execution_id, "step_1") is None
    assert resp.execution_id not in pipeline_executor._EXECUTION_CACHE


def test_memory_budget_eviction(monkeypatch):
    """Verify that executions are evicted when total cached memory exceeds MAX_EXECUTION_CACHE_TOTAL_BYTES."""
    pipeline_executor._EXECUTION_CACHE.clear()
    current_time = 1000.0
    monkeypatch.setattr(pipeline_executor.time, "time", lambda: current_time)

    # Set byte budget to 500 bytes (each 10x10 uint8 RGB image is 300 bytes)
    monkeypatch.setattr(pipeline_executor, "MAX_EXECUTION_CACHE_TOTAL_BYTES", 500)
    monkeypatch.setattr(pipeline_executor, "MAX_EXECUTION_CACHE_ENTRIES", 10)

    # Execution 1: ~300 bytes
    img1 = np.zeros((10, 10, 3), dtype=np.uint8)
    pipeline_executor._store_execution(
        "exec-1",
        {
            "block-1": {
                "index": 1,
                "block_id": "block-1",
                "type": "test",
                "image_array": img1,
                "image_format": "png",
                "timing_ms": 1.0,
            }
        },
    )
    assert "exec-1" in pipeline_executor._EXECUTION_CACHE

    current_time = 1001.0
    # Execution 2: ~300 bytes (Total now ~600 bytes > 500 byte limit -> exec-1 should be evicted)
    img2 = np.zeros((10, 10, 3), dtype=np.uint8)
    pipeline_executor._store_execution(
        "exec-2",
        {
            "block-2": {
                "index": 1,
                "block_id": "block-2",
                "type": "test",
                "image_array": img2,
                "image_format": "png",
                "timing_ms": 1.0,
            }
        },
    )

    assert "exec-1" not in pipeline_executor._EXECUTION_CACHE
    assert "exec-2" in pipeline_executor._EXECUTION_CACHE


def test_inspect_step_backward_compatibility():
    """Verify inspect_step works with both image_array (NumPy) and legacy image_bytes."""
    pipeline_executor._EXECUTION_CACHE.clear()
    img = np.full((10, 10, 3), 100, dtype=np.uint8)

    # 1. Stored as direct NumPy array
    pipeline_executor._store_execution(
        "numpy-exec",
        {
            "node_1": {
                "index": 1,
                "block_id": "node_1",
                "type": "test",
                "image_array": img,
                "image_format": "png",
                "timing_ms": 2.0,
            }
        },
    )
    res1 = inspect_step("numpy-exec", "node_1")
    assert res1 is not None
    assert res1["image"] is not None

    # 2. Stored as legacy compressed bytes
    legacy_bytes = pipeline_executor.encode_image_bytes(img, "png")
    pipeline_executor._store_execution(
        "legacy-exec",
        {
            "node_2": {
                "index": 1,
                "block_id": "node_2",
                "type": "test",
                "image_bytes": legacy_bytes,
                "image_format": "png",
                "timing_ms": 3.0,
            }
        },
    )
    res2 = inspect_step("legacy-exec", "node_2")
    assert res2 is not None
    assert res2["image"] is not None


def test_inspect_step_jpeg_lossy_fidelity():
    """Verify that inspecting a JPEG step returns analysis and histogram matching decoded JPEG image."""
    pipeline_executor._EXECUTION_CACHE.clear()
    img = np.random.randint(0, 256, (32, 32, 3), dtype=np.uint8)

    pipeline_executor._store_execution(
        "jpeg-exec",
        {
            "node_jpeg": {
                "index": 1,
                "block_id": "node_jpeg",
                "type": "test",
                "image_array": img,
                "image_format": "jpeg",
                "timing_ms": 1.5,
            }
        },
    )
    res = inspect_step("jpeg-exec", "node_jpeg")
    assert res is not None
    decoded_b64 = decode_base64_image(res["image"])
    assert res["analysis"].width == decoded_b64.shape[1]
    assert res["analysis"].height == decoded_b64.shape[0]
    expected_mean, _ = cv2.meanStdDev(decoded_b64)
    expected_mean_list = [float(v) for v in expected_mean.flatten()]
    for calculated_val, expected_val in zip(res["analysis"].mean, expected_mean_list, strict=False):
        assert abs(calculated_val - expected_val) < 1e-4


def test_pipeline_replaces_duplicate_block_id_cache_entry(sample_image_b64: str, monkeypatch):
    """Verify that replacing a duplicate block_id accounts for previous bytes correctly against memory ceiling."""
    # sample_image_b64 is 100x100
    one_image_bytes = 100 * 100 * 3
    monkeypatch.setattr(pipeline_executor, "MAX_EXECUTION_CACHE_TOTAL_BYTES", int(one_image_bytes * 1.5))
    monkeypatch.setattr(pipeline_executor, "MAX_EXECUTION_CACHE_PER_RUN_BYTES", int(one_image_bytes * 1.5))

    req = PipelineRequest(
        image=sample_image_b64,
        image_format="png",
        pipeline=[
            PipelineStep(block_id="dup_block", type="imageconversions_grayimage"),
            PipelineStep(
                block_id="dup_block",
                type="blurring_applygaussianblur",
                params={"widthSize": 3, "heightSize": 3},
            ),
        ],
    )
    resp = execute_pipeline(req)
    assert resp.success is True
    # The second step replaces the first with the same block_id, so it should still fit under the ceiling
    assert resp.step_results[0].has_full_image is True
    assert resp.step_results[1].has_full_image is True


def test_tiered_cache_falls_back_to_compressed_bytes_when_raw_budget_exhausted(sample_image_b64: str, monkeypatch):
    """Verify that when raw NumPy array budget is exceeded, caching falls back to compressed PNG bytes."""
    # Set raw budget low (5 KB) so raw array (~10 KB) overflows raw budget,
    # but total budget fits compressed bytes (~1-2 KB)
    monkeypatch.setattr(pipeline_executor, "MAX_EXECUTION_CACHE_RAW_PER_RUN_BYTES", 5 * 1024)
    monkeypatch.setattr(pipeline_executor, "MAX_EXECUTION_CACHE_PER_RUN_BYTES", 500 * 1024)

    req = PipelineRequest(
        image=sample_image_b64,
        image_format="png",
        pipeline=[
            PipelineStep(block_id="step_raw_overflow", type="imageconversions_grayimage"),
        ],
    )
    resp = execute_pipeline(req)
    assert resp.success is True
    assert resp.step_results[0].has_full_image is True

    # Check cached entry in _EXECUTION_CACHE: should have fallen back to image_bytes (compressed)
    cached_steps = pipeline_executor._EXECUTION_CACHE[resp.execution_id]["steps"]
    cached_entry = cached_steps["step_raw_overflow"]
    assert "image_bytes" in cached_entry
    assert isinstance(cached_entry["image_bytes"], bytes)
    assert "image_array" not in cached_entry

    # Inspect endpoint still works seamlessly
    inspected = inspect_step(resp.execution_id, "step_raw_overflow")
    assert inspected is not None
    assert inspected["image"] is not None


def test_step_beyond_per_run_budget_gets_has_full_image_false(sample_image_b64: str, monkeypatch):
    """Verify that steps exceeding total per-run budget get has_full_image=False while earlier steps are inspectable."""
    # Set per-run budget very small (50 bytes) so no steps fit
    monkeypatch.setattr(pipeline_executor, "MAX_EXECUTION_CACHE_PER_RUN_BYTES", 50)
    monkeypatch.setattr(pipeline_executor, "MAX_EXECUTION_CACHE_RAW_PER_RUN_BYTES", 50)

    req = PipelineRequest(
        image=sample_image_b64,
        image_format="png",
        pipeline=[
            PipelineStep(block_id="overbudget_step", type="imageconversions_grayimage"),
        ],
    )
    resp = execute_pipeline(req)
    assert resp.success is True
    assert resp.step_results[0].has_full_image is False

    # Execution is not inspectable
    inspected = inspect_step(resp.execution_id, "overbudget_step")
    assert inspected is None


def test_duplicate_block_id_clears_previous_entry_when_replacement_exceeds_budget(sample_image_b64: str, monkeypatch):
    """Verify that if a replacement cannot be cached, the earlier entry is pruned to avoid serving stale images."""
    one_image_bytes = 100 * 100 * 3
    # Step 1 fits in raw budget
    monkeypatch.setattr(pipeline_executor, "MAX_EXECUTION_CACHE_RAW_PER_RUN_BYTES", one_image_bytes + 1000)
    monkeypatch.setattr(pipeline_executor, "MAX_EXECUTION_CACHE_PER_RUN_BYTES", one_image_bytes + 1000)

    real_get_op = pipeline_executor.get_operator

    def hook_get_operator(step_type):
        op = real_get_op(step_type)
        if step_type == "blurring_applygaussianblur":
            # For step 2, lower budget to 0 so replacement cannot cache
            monkeypatch.setattr(pipeline_executor, "MAX_EXECUTION_CACHE_PER_RUN_BYTES", 0)
            monkeypatch.setattr(pipeline_executor, "MAX_EXECUTION_CACHE_RAW_PER_RUN_BYTES", 0)
        return op

    monkeypatch.setattr(pipeline_executor, "get_operator", hook_get_operator)

    req = PipelineRequest(
        image=sample_image_b64,
        image_format="png",
        pipeline=[
            PipelineStep(block_id="stale_test", type="imageconversions_grayimage"),
            PipelineStep(
                block_id="stale_test",
                type="blurring_applygaussianblur",
                params={"widthSize": 3, "heightSize": 3},
            ),
        ],
    )

    resp = execute_pipeline(req)
    assert resp.success is True
    assert resp.step_results[0].has_full_image is True
    # Step 2 exceeded budget
    assert resp.step_results[1].has_full_image is False

    # The stale entry for stale_test should have been pruned!
    inspected = inspect_step(resp.execution_id, "stale_test")
    assert inspected is None


def test_store_execution_drops_execution_exceeding_total_budget_without_clearing_cache():
    """Verify that an execution exceeding total budget returns early without evicting active cache entries."""
    pipeline_executor._EXECUTION_CACHE.clear()

    # Store a valid execution
    img_small = np.full((10, 10, 3), 120, dtype=np.uint8)
    pipeline_executor._store_execution(
        "valid-active-exec",
        {
            "node_1": {
                "index": 1,
                "block_id": "node_1",
                "type": "test",
                "image_array": img_small,
                "image_format": "png",
                "timing_ms": 1.0,
            }
        },
    )
    assert "valid-active-exec" in pipeline_executor._EXECUTION_CACHE

    # Attempt to store an oversized execution larger than MAX_EXECUTION_CACHE_TOTAL_BYTES
    oversized_steps = {
        "node_huge": {
            "index": 1,
            "block_id": "node_huge",
            "type": "test",
            "image_bytes": b"x" * (pipeline_executor.MAX_EXECUTION_CACHE_TOTAL_BYTES + 1024),
            "image_format": "png",
            "timing_ms": 2.0,
        }
    }
    pipeline_executor._store_execution("huge-oversized-exec", oversized_steps)

    # Oversized execution was rejected, and valid execution was NOT evicted
    assert "huge-oversized-exec" not in pipeline_executor._EXECUTION_CACHE
    assert "valid-active-exec" in pipeline_executor._EXECUTION_CACHE


def test_get_entry_bytes_and_standard_dict_caching():
    """Verify _get_entry_bytes correctly calculates size for image_array, image_bytes, and empty dicts."""
    from app.services.pipeline_executor import _get_entry_bytes

    # 1. NumPy array
    img = np.full((20, 20, 3), 50, dtype=np.uint8)
    arr_entry = {
        "index": 1,
        "block_id": "b1",
        "type": "test",
        "image_array": img,
        "image_format": "png",
        "timing_ms": 1.0,
    }
    total_bytes, raw_bytes = _get_entry_bytes(arr_entry)
    assert total_bytes == img.nbytes
    assert raw_bytes == img.nbytes

    # 2. Compressed bytes
    b_entry = {
        "index": 2,
        "block_id": "b2",
        "type": "test",
        "image_bytes": b"compressed_png_data",
        "image_format": "png",
        "timing_ms": 1.0,
    }
    total_bytes, raw_bytes = _get_entry_bytes(b_entry)
    assert total_bytes == len(b"compressed_png_data")
    assert raw_bytes == 0

    # 3. None or invalid entry
    assert _get_entry_bytes(None) == (0, 0)
    assert _get_entry_bytes({}) == (0, 0)


def test_parse_cache_byte_limit_validation(monkeypatch):
    """Verify _parse_cache_byte_limit safely validates env inputs with fallbacks."""
    from app.services.pipeline_executor import _parse_cache_byte_limit

    # Default returned when env not set
    assert _parse_cache_byte_limit("NON_EXISTENT_VAR_12345", 500) == 500

    # Non-numeric string falls back to default
    monkeypatch.setenv("TEST_CACHE_VAR", "invalid-string")
    assert _parse_cache_byte_limit("TEST_CACHE_VAR", 500) == 500

    # Zero or negative number falls back to default
    monkeypatch.setenv("TEST_CACHE_VAR", "0")
    assert _parse_cache_byte_limit("TEST_CACHE_VAR", 500) == 500
    monkeypatch.setenv("TEST_CACHE_VAR", "-50")
    assert _parse_cache_byte_limit("TEST_CACHE_VAR", 500) == 500

    # Valid positive integer parsed correctly
    monkeypatch.setenv("TEST_CACHE_VAR", " 2097152 ")
    assert _parse_cache_byte_limit("TEST_CACHE_VAR", 500) == 2097152

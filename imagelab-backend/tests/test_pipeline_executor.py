import base64

import numpy as np

from app.models.pipeline import PipelineRequest, PipelineStep
from app.services import pipeline_executor
from app.services.pipeline_executor import execute_pipeline
from app.utils.image import decode_base64_image


def cached_step(block_id="block"):
    return {
        "index": 1,
        "block_id": block_id,
        "type": "imageconvertions_grayimage",
        "image": np.zeros((2, 2, 3), dtype=np.uint8),
        "image_format": "png",
        "timing_ms": 1.0,
    }


def test_empty_pipeline(make_request):
    res = execute_pipeline(make_request([]))
    assert res.success is True
    assert res.image is not None


def test_noop_steps_are_skipped(make_request, sample_image_b64):
    steps = [
        PipelineStep(type="basic_readimage"),
        PipelineStep(type="basic_writeimage"),
    ]
    res = execute_pipeline(make_request(steps))
    assert res.success is True
    # NOOP steps should leave the image bytes unchanged
    assert res.image == sample_image_b64


def test_single_operator(make_request):
    steps = [PipelineStep(type="imageconvertions_grayimage", block_id="gray-block")]
    res = execute_pipeline(make_request(steps))
    assert res.success is True
    assert res.execution_id is not None
    assert len(res.step_results) == 1
    assert res.step_results[0].block_id == "gray-block"
    assert res.step_results[0].thumbnail is not None
    assert res.step_results[0].has_full_image is True
    # grayscale output should be 2-D or single-channel 3-D
    output = decode_base64_image(res.image)
    assert output.ndim == 2 or (output.ndim == 3 and output.shape[2] == 1), "expected grayscale output"


def test_multi_step_pipeline(make_request, sample_image_b64):
    steps = [
        PipelineStep(type="imageconvertions_grayimage", block_id="gray-block"),
        PipelineStep(
            type="blurring_applygaussianblur",
            block_id="blur-block",
            params={"widthSize": 3, "heightSize": 3},
        ),
    ]
    res = execute_pipeline(make_request(steps))
    assert res.success is True
    assert res.image is not None
    assert [step.block_id for step in res.step_results] == ["gray-block", "blur-block"]
    assert res.image != sample_image_b64  # blurred grayscale must differ from original


def test_unknown_operator_gives_clear_error(make_request):
    res = execute_pipeline(make_request([PipelineStep(type="not_a_real_op", block_id="bad-block")]))
    assert res.success is False
    assert res.step == 1
    assert res.error_block_id == "bad-block"
    assert len(res.step_results) == 1
    assert res.step_results[0].success is False
    assert "at step 1" in res.error
    assert "not_a_real_op" in res.error
    assert "Unknown operator" in res.error


def test_error_includes_correct_step_index(make_request):
    steps = [
        PipelineStep(type="imageconvertions_grayimage", block_id="gray-block"),
        PipelineStep(type="bad_operator_step_one", block_id="bad-block"),
    ]
    res = execute_pipeline(make_request(steps))
    assert res.success is False
    assert res.step == 2  # first step succeeds, second (1-indexed: 2) should fail
    assert res.error_block_id == "bad-block"
    assert len(res.step_results) == 2
    assert res.step_results[1].success is False
    assert "at step 2" in res.error
    assert "bad_operator_step_one" in res.error


def test_bad_image_data_fails_at_decode():
    req = PipelineRequest(image="!!!invalid_base64!!!", pipeline=[])
    res = execute_pipeline(req)
    assert res.success is False
    assert res.step == 0  # 0 = decode phase, before any pipeline step runs
    assert "decode" in res.error.lower() or "base64" in res.error.lower()


def test_valid_base64_but_invalid_image_fails():
    garbage = base64.b64encode(b"this is not image data").decode()
    req = PipelineRequest(image=garbage, pipeline=[])
    res = execute_pipeline(req)
    assert res.success is False
    assert res.step == 0


def test_pipeline_is_deterministic(make_request):
    steps = [PipelineStep(type="imageconvertions_grayimage")]
    r1 = execute_pipeline(make_request(steps))
    r2 = execute_pipeline(make_request(steps))
    assert r1.success is True
    assert r2.success is True
    assert r1.image == r2.image


def test_execution_cache_evicts_expired_entries(monkeypatch):
    pipeline_executor._EXECUTION_CACHE.clear()
    current_time = 1000.0

    monkeypatch.setattr(pipeline_executor, "EXECUTION_CACHE_TTL_SECONDS", 10)
    monkeypatch.setattr(pipeline_executor.time, "time", lambda: current_time)
    pipeline_executor._store_execution("old-execution", {"block": cached_step()})

    current_time = 1011.0

    assert pipeline_executor.inspect_step("old-execution", "block") is None
    assert "old-execution" not in pipeline_executor._EXECUTION_CACHE


def test_execution_cache_updates_last_accessed_on_inspect(monkeypatch):
    pipeline_executor._EXECUTION_CACHE.clear()
    current_time = 1000.0

    monkeypatch.setattr(pipeline_executor.time, "time", lambda: current_time)
    pipeline_executor._store_execution("execution", {"block": cached_step()})

    current_time = 1005.0

    assert pipeline_executor.inspect_step("execution", "block") is not None
    assert pipeline_executor._EXECUTION_CACHE["execution"]["last_accessed_at"] == 1005.0


def test_execution_cache_evicts_least_recently_used_entry_when_max_exceeded(monkeypatch):
    pipeline_executor._EXECUTION_CACHE.clear()
    current_time = 1000.0

    monkeypatch.setattr(pipeline_executor, "MAX_EXECUTION_CACHE_ENTRIES", 2)
    monkeypatch.setattr(pipeline_executor.time, "time", lambda: current_time)

    pipeline_executor._store_execution("execution-1", {"block-1": cached_step("block-1")})
    current_time = 1001.0
    pipeline_executor._store_execution("execution-2", {"block-2": cached_step("block-2")})
    current_time = 1002.0
    assert pipeline_executor.inspect_step("execution-1", "block-1") is not None
    current_time = 1003.0
    pipeline_executor._store_execution("execution-3", {"block-3": cached_step("block-3")})

    assert "execution-2" not in pipeline_executor._EXECUTION_CACHE
    assert set(pipeline_executor._EXECUTION_CACHE) == {"execution-1", "execution-3"}

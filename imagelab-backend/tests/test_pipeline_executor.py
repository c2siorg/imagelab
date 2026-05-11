import base64

from app.models.pipeline import PipelineRequest, PipelineStep
from app.services.pipeline_executor import execute_pipeline
from app.utils.image import decode_base64_image


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
    steps = [PipelineStep(type="imageconvertions_grayimage")]
    res = execute_pipeline(make_request(steps))
    assert res.success is True
    # grayscale output should be 2-D or single-channel 3-D
    output = decode_base64_image(res.image)
    assert output.ndim == 2 or (output.ndim == 3 and output.shape[2] == 1), "expected grayscale output"


def test_multi_step_pipeline(make_request, sample_image_b64):
    steps = [
        PipelineStep(type="imageconvertions_grayimage"),
        PipelineStep(type="blurring_applygaussianblur", params={"widthSize": 3, "heightSize": 3}),
    ]
    res = execute_pipeline(make_request(steps))
    assert res.success is True
    assert res.image is not None
    assert res.image != sample_image_b64  # blurred grayscale must differ from original


def test_unknown_operator_gives_clear_error(make_request):
    res = execute_pipeline(make_request([PipelineStep(type="not_a_real_op")]))
    assert res.success is False
    assert res.step == 1
    assert "at step 1" in res.error
    assert "not_a_real_op" in res.error
    assert "Unknown operator" in res.error


def test_error_includes_correct_step_index(make_request):
    steps = [
        PipelineStep(type="imageconvertions_grayimage"),
        PipelineStep(type="bad_operator_step_one"),
    ]
    res = execute_pipeline(make_request(steps))
    assert res.success is False
    assert res.step == 2  # first step succeeds, second (1-indexed: 2) should fail
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

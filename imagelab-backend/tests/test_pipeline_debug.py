"""Tests for the debug mode pipeline execution."""

EXECUTE_URL = "/api/pipeline/execute"

GRAY_STEP = {"type": "imageconvertions_grayimage", "params": {}}
BLUR_STEP = {"type": "blurring_applygaussianblur", "params": {"widthSize": 3, "heightSize": 3}}
NOOP_STEP = {"type": "basic_readimage", "params": {}}


def post(client, png_b64, pipeline, debug=False):
    return client.post(
        EXECUTE_URL,
        json={"image": png_b64, "image_format": "png", "pipeline": pipeline, "debug": debug},
    )


def test_debug_false_returns_no_frames(client, png_b64):
    r = post(client, png_b64, [GRAY_STEP], debug=False)
    assert r.json()["debug_frames"] is None


def test_debug_omitted_returns_no_frames(client, png_b64):
    r = client.post(
        EXECUTE_URL,
        json={"image": png_b64, "image_format": "png", "pipeline": [GRAY_STEP]},
    )
    assert r.json()["debug_frames"] is None


def test_debug_true_single_step_returns_one_frame(client, png_b64):
    r = post(client, png_b64, [GRAY_STEP], debug=True)
    data = r.json()
    assert data["success"] is True
    assert data["debug_frames"] is not None
    assert len(data["debug_frames"]) == 1


def test_debug_frame_count_matches_non_noop_steps(client, png_b64):
    r = post(client, png_b64, [GRAY_STEP, BLUR_STEP], debug=True)
    data = r.json()
    assert data["success"] is True
    assert len(data["debug_frames"]) == 2


def test_noop_steps_excluded_from_debug_frames(client, png_b64):
    r = post(client, png_b64, [NOOP_STEP, GRAY_STEP], debug=True)
    data = r.json()
    assert data["success"] is True
    # NOOP_STEP is skipped — only GRAY_STEP produces a frame
    assert len(data["debug_frames"]) == 1


def test_debug_frames_are_valid_base64_strings(client, png_b64):
    import base64

    r = post(client, png_b64, [GRAY_STEP], debug=True)
    frame = r.json()["debug_frames"][0]
    # Should not raise
    decoded = base64.b64decode(frame)
    assert len(decoded) > 0


def test_debug_frames_differ_between_steps(client, png_b64):
    import base64
    import cv2
    import numpy as np

    # Non-uniform image so gaussian blur produces a visibly different result
    rng = np.random.default_rng(0)
    img = rng.integers(0, 256, (50, 50, 3), dtype=np.uint8)
    _, buf = cv2.imencode(".png", img)
    noisy_b64 = base64.b64encode(buf.tobytes()).decode()

    r = post(client, noisy_b64, [GRAY_STEP, BLUR_STEP], debug=True)
    data = r.json()
    assert data["debug_frames"][0] != data["debug_frames"][1]


def test_last_debug_frame_matches_final_image(client, png_b64):
    r = post(client, png_b64, [GRAY_STEP, BLUR_STEP], debug=True)
    data = r.json()
    assert data["debug_frames"][-1] == data["image"]


def test_debug_on_empty_pipeline_returns_empty_frames(client, png_b64):
    r = post(client, png_b64, [], debug=True)
    data = r.json()
    assert data["success"] is True
    assert data["debug_frames"] == []


def test_debug_on_failure_returns_no_frames(client, png_b64):
    bad_step = {"type": "not_a_real_operator", "params": {}}
    r = post(client, png_b64, [bad_step], debug=True)
    data = r.json()
    assert data["success"] is False
    assert data["debug_frames"] is None

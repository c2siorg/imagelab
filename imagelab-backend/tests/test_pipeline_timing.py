EXECUTE_URL = "/api/pipeline/execute"

GRAY_STEP = {"type": "imageconvertions_grayimage", "params": {}}
BINARY_STEP = {"type": "imageconvertions_graytobinary", "params": {"thresholdValue": 127, "maxValue": 255}}
NOOP_STEP = {"type": "basic_readimage", "params": {}}


def post(client, png_b64, pipeline):
    return client.post(EXECUTE_URL, json={"image": png_b64, "image_format": "png", "pipeline": pipeline})


def test_successful_pipeline_includes_timings(client, png_b64):
    r = post(client, png_b64, [GRAY_STEP])
    data = r.json()
    assert data["success"] is True
    assert data["timings"] is not None
    assert data["timings"]["total_ms"] > 0
    assert len(data["timings"]["steps"]) == 1
    assert data["timings"]["steps"][0]["step"] == 1
    assert data["timings"]["steps"][0]["operator_type"] == GRAY_STEP["type"]


def test_partial_timings_returned_on_failure(client, png_b64):
    bad_step = {"type": "not_a_real_operator", "params": {}}
    # First step succeeds, second is unknown — partial timing for step 1 must be present
    r = post(client, png_b64, [GRAY_STEP, bad_step])
    data = r.json()
    assert data["success"] is False
    assert data["timings"] is not None
    assert len(data["timings"]["steps"]) == 1
    assert data["timings"]["steps"][0]["step"] == 1


def test_noop_steps_excluded_from_timings(client, png_b64):
    r = post(client, png_b64, [NOOP_STEP])
    data = r.json()
    assert data["success"] is True
    assert data["timings"]["steps"] == []


def test_step_numbers_are_1_indexed(client, png_b64):
    r = post(client, png_b64, [GRAY_STEP, BINARY_STEP])
    data = r.json()
    assert data["success"] is True
    steps = data["timings"]["steps"]
    assert steps[0]["step"] == 1
    assert steps[1]["step"] == 2


def test_error_step_is_1_indexed(client, png_b64):
    bad_step = {"type": "not_a_real_operator", "params": {}}
    r = post(client, png_b64, [bad_step])
    data = r.json()
    assert data["success"] is False
    assert data["step"] == 1

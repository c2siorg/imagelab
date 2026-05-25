EXECUTE_URL = "/api/v1/pipeline/executions"

GRAY_STEP = {"type": "imageconvertions_grayimage", "params": {}}
GRAY_STEP_WITH_ID = {"type": "imageconvertions_grayimage", "block_id": "gray-block", "params": {}}
BINARY_STEP = {"type": "imageconvertions_graytobinary", "params": {"thresholdValue": 127, "maxValue": 255}}


def post(client, png_b64, pipeline):
    return client.post(EXECUTE_URL, json={"image": png_b64, "image_format": "png", "pipeline": pipeline})


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_legacy_execute_endpoint_removed(client, png_b64):
    r = client.post(
        "/api/pipeline/execute",
        json={"image": png_b64, "image_format": "png", "pipeline": [GRAY_STEP]},
    )
    assert r.status_code == 404


def test_single_step(client, png_b64):
    r = post(client, png_b64, [GRAY_STEP_WITH_ID])
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True
    assert data["image"] is not None
    assert data["execution_id"] is not None
    assert data["step_results"][0]["block_id"] == "gray-block"
    assert data["step_results"][0]["thumbnail"] is not None


def test_multi_step(client, png_b64):
    r = post(client, png_b64, [GRAY_STEP, BINARY_STEP])
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True
    assert data["image"] is not None


def test_empty_pipeline(client, png_b64):
    r = post(client, png_b64, [])
    assert r.status_code == 200
    assert r.json()["success"] is True


def test_unknown_operator(client, png_b64):
    bad_step = {"type": "not_a_real_operator", "params": {}}
    r = post(client, png_b64, [bad_step])
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is False
    assert "not_a_real_operator" in data["error"]


def test_invalid_base64(client):
    r = client.post(
        EXECUTE_URL, json={"image": "!!!not_valid_base64!!!", "image_format": "png", "pipeline": [GRAY_STEP]}
    )
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is False
    assert "Failed to decode image" in data["error"]


def test_missing_image_field(client):
    r = client.post(EXECUTE_URL, json={"image_format": "png", "pipeline": [GRAY_STEP]})
    assert r.status_code == 422
    assert "detail" in r.json()


def test_missing_pipeline_field(client):
    r = client.post(EXECUTE_URL, json={"image": "abc", "image_format": "png"})
    assert r.status_code == 422
    assert "detail" in r.json()


def test_large_pipeline(client, png_b64):
    # grayimage first, then many binary thresholds — each step works on a 2D image
    pipeline = [GRAY_STEP] + [BINARY_STEP] * 10
    r = post(client, png_b64, pipeline)
    assert r.status_code == 200
    assert r.json()["success"] is True


def test_error_response_has_step(client, png_b64):
    bad_step = {"type": "not_a_real_operator", "params": {}}
    r = post(client, png_b64, [bad_step])
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is False
    assert isinstance(data["step"], int)


def test_execution_inspect_returns_full_image_and_analysis(client, png_b64):
    r = client.post(
        "/api/v1/pipeline/executions",
        json={"image": png_b64, "image_format": "png", "pipeline": [GRAY_STEP_WITH_ID]},
    )
    assert r.status_code == 200
    execution = r.json()
    inspect = client.get(
        f"/api/v1/pipeline/executions/{execution['execution_id']}/steps/inspect",
        params={"block_id": "gray-block"},
    )
    assert inspect.status_code == 200
    data = inspect.json()
    assert data["success"] is True
    assert data["block_id"] == "gray-block"
    assert data["image"] is not None
    assert data["analysis"]["width"] == 10
    assert data["analysis"]["height"] == 10


def test_execution_inspect_supports_block_ids_with_slashes(client, png_b64):
    step = {"type": "imageconvertions_grayimage", "block_id": "block/with/slash", "params": {}}
    r = client.post(
        "/api/v1/pipeline/executions",
        json={"image": png_b64, "image_format": "png", "pipeline": [step]},
    )
    assert r.status_code == 200
    execution = r.json()
    inspect = client.get(
        f"/api/v1/pipeline/executions/{execution['execution_id']}/steps/inspect",
        params={"block_id": "block/with/slash"},
    )
    assert inspect.status_code == 200
    assert inspect.json()["block_id"] == "block/with/slash"

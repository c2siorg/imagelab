EXECUTE_URL = "/api/pipeline/execute"

GRAY_STEP = {"type": "imageconvertions_grayimage", "params": {}}
BINARY_STEP = {"type": "imageconvertions_graytobinary", "params": {"thresholdValue": 127, "maxValue": 255}}


def post(client, png_b64, pipeline):
    return client.post(EXECUTE_URL, json={"image": png_b64, "image_format": "png", "pipeline": pipeline})


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_single_step(client, png_b64):
    r = post(client, png_b64, [GRAY_STEP])
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True
    assert data["image"] is not None


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

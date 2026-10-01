"""Tests for the face detection operator."""

from unittest.mock import MagicMock, patch

import cv2
import numpy as np
import pytest

from app.operators.detection.face_detection import FaceDetection, _get_face_cascade


def make_operator(params: dict | None = None):
    """Create a FaceDetection operator with params."""
    return FaceDetection(params or {})


def make_blank_image(channels=3, height=200, width=200, dtype=np.uint8):
    """Create a blank synthetic image with no detectable features."""
    if channels == 1:
        return np.full((height, width), 128, dtype=dtype)
    return np.full((height, width, channels), 128, dtype=dtype)


def make_synthetic_face_image(channels=3, dtype=np.uint8):
    """Create a synthetic image containing a detectable frontal face for end-to-end cascade testing."""
    canvas = np.full((300, 300), 200, dtype=np.uint8)
    cv2.ellipse(canvas, (150, 150), (80, 100), 0, 0, 360, 180, -1)
    cv2.circle(canvas, (120, 120), 15, 50, -1)
    cv2.circle(canvas, (180, 120), 15, 50, -1)
    cv2.line(canvas, (100, 100), (135, 105), 30, 4)
    cv2.line(canvas, (165, 105), (200, 100), 30, 4)
    cv2.line(canvas, (150, 130), (150, 160), 60, 3)
    cv2.ellipse(canvas, (150, 185), (30, 10), 0, 0, 180, 40, -1)

    if channels == 1:
        img = canvas
    elif channels == 3:
        img = cv2.cvtColor(canvas, cv2.COLOR_GRAY2BGR)
    else:  # 4-channel BGRA
        img = cv2.cvtColor(canvas, cv2.COLOR_GRAY2BGRA)

    if dtype == np.float32:
        return (img.astype(np.float32) / 255.0).clip(0.0, 1.0)
    elif dtype == np.uint16:
        return (img.astype(np.uint16) << 8) | img.astype(np.uint16)
    return img


@pytest.mark.parametrize(
    "params",
    [
        {},  # defaults
        {"scaleFactor": 1.1, "minNeighbors": 5, "minWidth": 30, "minHeight": 30},
        {"rgbcolors_input": "#FF0000", "thickness": 3},
        {"minSize": 25},
    ],
)
def test_face_detection_returns_valid_image(params):
    """Operator should return an image with same shape and dtype on blank input."""
    image = make_blank_image(channels=3)
    op = make_operator(params)

    result = op.compute(image.copy())

    assert result.shape == image.shape
    assert result.dtype == image.dtype


@pytest.mark.parametrize("channels", [1, 3, 4])
def test_face_detection_supports_gray_bgr_bgra(channels):
    """Operator should accept grayscale, BGR, and BGRA inputs and return unchanged when no detections."""
    image = make_blank_image(channels=channels)
    op = make_operator({})

    result = op.compute(image.copy())

    assert result.shape == image.shape
    assert result.dtype == image.dtype


def test_no_detections_returns_unchanged():
    """Image with no faces should return the original image unchanged."""
    image = make_blank_image(channels=3)
    op = make_operator({})

    result = op.compute(image.copy())

    np.testing.assert_array_equal(result, image)


def test_does_not_mutate_input():
    """Operator should not modify the input image array."""
    image = make_blank_image(channels=3)
    original = image.copy()
    op = make_operator({})

    _ = op.compute(image)

    np.testing.assert_array_equal(image, original)


@pytest.mark.parametrize(
    "param_name,invalid_value,error_match",
    [
        ("scaleFactor", 0.5, "scaleFactor must be between 1.01 and 2.0"),
        ("scaleFactor", 3.0, "scaleFactor must be between 1.01 and 2.0"),
        ("minNeighbors", 0, "minNeighbors must be between 1 and 20"),
        ("minNeighbors", 25, "minNeighbors must be between 1 and 20"),
        ("minWidth", 5, "minWidth must be between 10 and 500"),
        ("minWidth", 600, "minWidth must be between 10 and 500"),
        ("minHeight", 5, "minHeight must be between 10 and 500"),
        ("minHeight", 600, "minHeight must be between 10 and 500"),
        ("thickness", 0, "thickness must be between 1 and 10"),
        ("thickness", 15, "thickness must be between 1 and 10"),
    ],
)
def test_invalid_parameters_raise(param_name, invalid_value, error_match):
    """Invalid parameter values should raise ValueError with descriptive message."""
    params = {param_name: invalid_value}
    op = make_operator(params)

    with pytest.raises(ValueError, match=error_match):
        op.compute(make_blank_image())


def test_unsupported_image_shape_raises():
    """Images with unsupported shapes should raise ValueError."""
    image = np.zeros((100, 100, 5), dtype=np.uint8)
    op = make_operator({})

    with pytest.raises(ValueError, match="Unsupported image shape"):
        op.compute(image)


def test_grayscale_2d_image_no_detections():
    """2D grayscale images (H, W) with no detections should return matching shape and dtype."""
    image = make_blank_image(channels=1).squeeze()
    assert len(image.shape) == 2

    op = make_operator({})
    result = op.compute(image.copy())

    assert result.shape == image.shape
    assert result.dtype == image.dtype
    np.testing.assert_array_equal(result, image)


def test_cascade_initialization():
    """Operator should successfully load Haar cascade file."""
    op = make_operator({})
    assert not op.face_cascade.empty()


def test_cascade_initialization_failure_raises():
    """Operator should raise ValueError if Haar cascade file fails to load."""
    _get_face_cascade.cache_clear()
    with patch("cv2.CascadeClassifier") as mock_classifier:
        mock_instance = MagicMock()
        mock_instance.empty.return_value = True
        mock_classifier.return_value = mock_instance

        with pytest.raises(ValueError, match="Failed to load face cascade"):
            FaceDetection({})
    _get_face_cascade.cache_clear()


def test_different_box_colors():
    """Different box colors should be accepted without error."""
    colors = ["#FF0000", "#00FF00", "#0000FF", "#FFFF00"]
    image = make_blank_image(channels=3)

    for color in colors:
        op = make_operator({"rgbcolors_input": color})
        result = op.compute(image.copy())
        assert result.shape == image.shape


def test_float_images_with_no_detections():
    """Float images should be handled and on no detections return same shape and dtype."""
    image = np.ones((100, 100, 3), dtype=np.float32) * 0.5
    op = make_operator({})

    result = op.compute(image.copy())

    assert result.dtype == np.float32
    assert result.shape == (100, 100, 3)
    np.testing.assert_array_equal(result, image)


def test_uint16_images_with_no_detections():
    """uint16 images should be handled and on no detections return same shape and dtype."""
    image = np.ones((100, 100, 3), dtype=np.uint16) * 32768
    op = make_operator({})

    result = op.compute(image.copy())

    assert result.dtype == np.uint16
    assert result.shape == (100, 100, 3)
    np.testing.assert_array_equal(result, image)


def test_detections_drawn_on_bgr_image():
    """Simulated face detections should draw bounding boxes with user-specified color."""
    op = make_operator({"rgbcolors_input": "#00FF00", "thickness": 2})
    image = make_blank_image(channels=3, height=200, width=200)

    # Mock face_cascade to return two detected faces
    op.face_cascade = MagicMock()
    op.face_cascade.detectMultiScale.return_value = np.array([[30, 40, 50, 50], [120, 40, 50, 50]])

    result = op.compute(image.copy())

    assert result.dtype == np.uint8
    assert result.shape == (200, 200, 3)

    # Box color is green (#00FF00 -> BGR (0, 255, 0))
    has_green = np.any((result[:, :, 0] == 0) & (result[:, :, 1] == 255) & (result[:, :, 2] == 0))
    assert has_green, "Face bounding box with user color was not drawn"


def test_detections_drawn_on_grayscale_image():
    """When faces are detected on a grayscale image, output is promoted to BGR for colored boxes."""
    op = make_operator({"rgbcolors_input": "#FF0000"})
    image = make_blank_image(channels=1, height=200, width=200)

    op.face_cascade = MagicMock()
    op.face_cascade.detectMultiScale.return_value = np.array([[50, 50, 60, 60]])

    result = op.compute(image.copy())

    assert result.dtype == np.uint8
    assert result.shape == (200, 200, 3)

    # Color is red (#FF0000 -> BGR (0, 0, 255))
    has_red = np.any((result[:, :, 0] == 0) & (result[:, :, 1] == 0) & (result[:, :, 2] == 255))
    assert has_red, "Face bounding box with user color was not drawn on promoted BGR image"


def test_detections_drawn_on_bgra_image():
    """When faces are detected on a BGRA image, output retains 4 channels with alpha."""
    op = make_operator({"rgbcolors_input": "#0000FF"})
    image = make_blank_image(channels=4, height=200, width=200)

    op.face_cascade = MagicMock()
    op.face_cascade.detectMultiScale.return_value = np.array([[50, 50, 60, 60]])

    result = op.compute(image.copy())

    assert result.dtype == np.uint8
    assert result.shape == (200, 200, 4)

    # Color is blue (#0000FF -> BGRA (255, 0, 0, 255))
    has_blue = np.any(
        (result[:, :, 0] == 255) & (result[:, :, 1] == 0) & (result[:, :, 2] == 0) & (result[:, :, 3] == 255)
    )
    assert has_blue, "Face bounding box with user color was not drawn on BGRA image"


@pytest.mark.parametrize("dtype", [np.float32, np.uint16, np.uint8])
@pytest.mark.parametrize("channels", [1, 3, 4])
def test_detections_preserve_input_dtype(dtype, channels):
    """When faces are detected, output dtype must match input dtype across all channel configurations."""
    op = make_operator({"rgbcolors_input": "#00FF00", "thickness": 2})
    image = make_blank_image(channels=channels, height=200, width=200, dtype=dtype)
    if dtype == np.float32:
        image = image / 255.0

    op.face_cascade = MagicMock()
    op.face_cascade.detectMultiScale.return_value = np.array([[20, 20, 40, 40]])

    result = op.compute(image.copy())

    assert result.dtype == dtype, f"Expected output dtype {dtype}, got {result.dtype}"
    expected_channels = 3 if channels == 1 else channels
    expected_shape = (200, 200) if expected_channels == 1 else (200, 200, expected_channels)
    assert result.shape == expected_shape


def test_real_haar_cascade_detects_face_end_to_end():
    """Exercise the real OpenCV Haar cascade, histogram equalization, and bounding box drawing on a face image."""
    image = make_synthetic_face_image(channels=3, dtype=np.uint8)
    op = make_operator({"scaleFactor": 1.1, "minNeighbors": 5, "minWidth": 30, "minHeight": 30})

    result = op.compute(image)

    # Output dtype and shape must be preserved
    assert result.dtype == np.uint8
    assert result.shape == image.shape
    # Bounding boxes were drawn, so the output must differ from the input
    assert not np.array_equal(result, image), "Real Haar cascade should detect face and draw bounding box"


@pytest.mark.parametrize("dtype", [np.float32, np.uint16])
def test_real_haar_cascade_non_uint8_end_to_end(dtype):
    """Exercise real Haar cascade detection on non-uint8 images, confirming detection and dtype preservation."""
    image = make_synthetic_face_image(channels=3, dtype=dtype)
    op = make_operator({"scaleFactor": 1.1, "minNeighbors": 5})

    result = op.compute(image)

    assert result.dtype == dtype
    assert result.shape == image.shape
    assert not np.array_equal(result, image)


def test_histogram_equalization_used():
    """Verify that histogram equalization is applied before detection."""
    op = make_operator({})
    image = make_blank_image(channels=3)

    with patch("cv2.equalizeHist", wraps=cv2.equalizeHist) as mock_equalize:
        _ = op.compute(image)
        assert mock_equalize.called, "cv2.equalizeHist should be called during detection"


def test_registry_registration():
    """Verify that detection_facedetection is registered in OPERATOR_REGISTRY."""
    from app.operators.registry import OPERATOR_REGISTRY, get_operator

    assert "detection_facedetection" in OPERATOR_REGISTRY
    assert get_operator("detection_facedetection") is FaceDetection


def test_pipeline_execution_with_face_detection(sample_image_b64):
    """Verify that detection_facedetection executes end-to-end in pipeline_executor."""
    from app.models.pipeline import PipelineRequest, PipelineStep
    from app.services.pipeline_executor import execute_pipeline

    request = PipelineRequest(
        image=sample_image_b64,
        image_format="png",
        pipeline=[PipelineStep(type="detection_facedetection", block_id="face-block-1", params={})],
    )
    result = execute_pipeline(request)
    assert result.success is True
    assert result.image is not None
    assert len(result.step_results) == 1
    assert result.step_results[0].block_id == "face-block-1"


def test_empty_image_returns_unchanged():
    """Empty image with zero dimensions should return a copy unchanged."""
    empty_image = np.zeros((0, 0, 3), dtype=np.uint8)
    op = make_operator({})
    result = op.compute(empty_image)
    assert result.shape == (0, 0, 3)


def test_default_parameters_passed_to_cascade():
    """Verify default scaleFactor, minNeighbors, and minSize (30, 30) are passed to detectMultiScale."""
    op = make_operator({})
    op.face_cascade = MagicMock()
    op.face_cascade.detectMultiScale.return_value = np.empty((0, 4), dtype=int)
    image = make_blank_image(channels=3)

    _ = op.compute(image)

    op.face_cascade.detectMultiScale.assert_called_once()
    _, kwargs = op.face_cascade.detectMultiScale.call_args
    assert kwargs["scaleFactor"] == 1.1
    assert kwargs["minNeighbors"] == 5
    assert kwargs["minSize"] == (30, 30)

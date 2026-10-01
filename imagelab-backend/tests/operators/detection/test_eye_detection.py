"""Tests for the eye detection operator."""

from unittest.mock import MagicMock, patch

import cv2
import numpy as np
import pytest

from app.operators.detection.eye_detection import EyeDetection


def make_operator(params: dict | None = None):
    """Create an EyeDetection operator with params."""
    return EyeDetection(params or {})


def make_blank_image(channels=3, height=200, width=200, dtype=np.uint8):
    """Create a blank synthetic image with no detectable features."""
    if channels == 1:
        return np.full((height, width), 128, dtype=dtype)
    return np.full((height, width, channels), 128, dtype=dtype)


@pytest.mark.parametrize(
    "params",
    [
        {},  # defaults
        {"scaleFactor": 1.1, "minNeighbors": 5, "minWidth": 30, "minHeight": 30},
        {"rgbcolors_input": "#FF0000", "thickness": 3},
        {"minSize": 25},
    ],
)
def test_eye_detection_returns_valid_image(params):
    """Operator should return an image with same shape and dtype on blank input."""
    image = make_blank_image(channels=3)
    op = make_operator(params)

    result = op.compute(image.copy())

    assert result.shape == image.shape
    assert result.dtype == image.dtype


@pytest.mark.parametrize("channels", [1, 3, 4])
def test_eye_detection_supports_gray_bgr_bgra(channels):
    """Operator should accept grayscale, BGR, and BGRA inputs and return unchanged when no detections."""
    image = make_blank_image(channels=channels)
    op = make_operator({})

    result = op.compute(image.copy())

    assert result.shape == image.shape
    assert result.dtype == image.dtype


def test_no_detections_returns_unchanged():
    """Image with no eyes should return the original image unchanged."""
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
    assert not op.eye_cascade.empty()


def test_cascade_initialization_failure_raises():
    """Operator should raise ValueError if Haar cascade file fails to load."""
    with patch("cv2.CascadeClassifier") as mock_classifier:
        mock_instance = MagicMock()
        mock_instance.empty.return_value = True
        mock_classifier.return_value = mock_instance

        with pytest.raises(ValueError, match="Failed to load eye cascade"):
            EyeDetection({})


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
    """Simulated eye detections should draw bounding boxes with user-specified color."""
    op = make_operator({"rgbcolors_input": "#00FF00", "thickness": 2})
    image = make_blank_image(channels=3, height=200, width=200)

    # Mock eye_cascade to return two detected eyes
    op.eye_cascade = MagicMock()
    op.eye_cascade.detectMultiScale.return_value = np.array([[30, 40, 30, 20], [120, 40, 30, 20]])

    result = op.compute(image.copy())

    assert result.dtype == np.uint8
    assert result.shape == (200, 200, 3)

    # Box color is green (#00FF00 -> BGR (0, 255, 0))
    has_green = np.any((result[:, :, 0] == 0) & (result[:, :, 1] == 255) & (result[:, :, 2] == 0))
    assert has_green, "Eye bounding box with user color was not drawn"


def test_detections_drawn_on_grayscale_image():
    """When eyes are detected on a grayscale image, output is promoted to BGR for colored boxes."""
    op = make_operator({"rgbcolors_input": "#FF0000"})
    image = make_blank_image(channels=1, height=200, width=200)

    op.eye_cascade = MagicMock()
    op.eye_cascade.detectMultiScale.return_value = np.array([[50, 50, 40, 30]])

    result = op.compute(image.copy())

    assert result.dtype == np.uint8
    assert result.shape == (200, 200, 3)

    # Color is red (#FF0000 -> BGR (0, 0, 255))
    has_red = np.any((result[:, :, 0] == 0) & (result[:, :, 1] == 0) & (result[:, :, 2] == 255))
    assert has_red, "Eye bounding box with user color was not drawn on promoted BGR image"


def test_detections_drawn_on_bgra_image():
    """When eyes are detected on a BGRA image, output retains 4 channels with alpha."""
    op = make_operator({"rgbcolors_input": "#0000FF"})
    image = make_blank_image(channels=4, height=200, width=200)

    op.eye_cascade = MagicMock()
    op.eye_cascade.detectMultiScale.return_value = np.array([[50, 50, 40, 30]])

    result = op.compute(image.copy())

    assert result.dtype == np.uint8
    assert result.shape == (200, 200, 4)

    # Color is blue (#0000FF -> BGRA (255, 0, 0, 255))
    has_blue = np.any(
        (result[:, :, 0] == 255) & (result[:, :, 1] == 0) & (result[:, :, 2] == 0) & (result[:, :, 3] == 255)
    )
    assert has_blue, "Eye bounding box with user color was not drawn on BGRA image"


def test_histogram_equalization_used():
    """Verify that histogram equalization is applied before detection."""
    op = make_operator({})
    image = make_blank_image(channels=3)

    with patch("cv2.equalizeHist", wraps=cv2.equalizeHist) as mock_equalize:
        _ = op.compute(image)
        assert mock_equalize.called, "cv2.equalizeHist should be called during detection"


def test_registry_registration():
    """Verify that detection_eyedetection is registered in OPERATOR_REGISTRY."""
    from app.operators.registry import OPERATOR_REGISTRY, get_operator

    assert "detection_eyedetection" in OPERATOR_REGISTRY
    assert get_operator("detection_eyedetection") is EyeDetection


def test_pipeline_execution_with_eye_detection(sample_image_b64):
    """Verify that detection_eyedetection executes end-to-end in pipeline_executor."""
    from app.models.pipeline import PipelineRequest, PipelineStep
    from app.services.pipeline_executor import execute_pipeline

    request = PipelineRequest(
        image=sample_image_b64,
        image_format="png",
        pipeline=[PipelineStep(type="detection_eyedetection", block_id="eye-block-1", params={})],
    )
    result = execute_pipeline(request)
    assert result.success is True
    assert result.image is not None
    assert len(result.step_results) == 1
    assert result.step_results[0].block_id == "eye-block-1"


def test_empty_image_returns_unchanged():
    """Empty image with zero dimensions should return a copy unchanged."""
    empty_image = np.zeros((0, 0, 3), dtype=np.uint8)
    op = make_operator({})
    result = op.compute(empty_image)
    assert result.shape == (0, 0, 3)


def test_default_parameters_passed_to_cascade():
    """Verify default scaleFactor, minNeighbors, and minSize (10, 10) are passed to detectMultiScale."""
    op = make_operator({})
    op.eye_cascade = MagicMock()
    op.eye_cascade.detectMultiScale.return_value = np.empty((0, 4), dtype=int)
    image = make_blank_image(channels=3)

    _ = op.compute(image)

    op.eye_cascade.detectMultiScale.assert_called_once()
    _, kwargs = op.eye_cascade.detectMultiScale.call_args
    assert kwargs["scaleFactor"] == 1.1
    assert kwargs["minNeighbors"] == 5
    assert kwargs["minSize"] == (10, 10)

"""Tests for the smile detection operator."""

import numpy as np
import pytest

from app.operators.detection.smile_detection import SmileDetection


def make_operator(params: dict):
    """Create a SmileDetection operator with params."""
    return SmileDetection(params or {})


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
        {"drawFaceBoxes": True},
    ],
)
def test_smile_detection_returns_valid_image(params):
    """Operator should return an image with same shape and dtype on blank input."""
    image = make_blank_image(channels=3)
    op = make_operator(params)

    result = op.compute(image.copy())

    assert result.shape == image.shape
    assert result.dtype == image.dtype


@pytest.mark.parametrize("channels", [1, 3, 4])
def test_smile_detection_supports_gray_bgr_bgra(channels):
    """Operator should process grayscale, BGR, and BGRA inputs."""
    image = make_blank_image(channels=channels)
    op = make_operator({})

    result = op.compute(image.copy())

    if channels == 1:
        # Grayscale input is promoted to BGR for colored bounding boxes
        assert result.shape == (200, 200, 3)
    else:
        # BGR (3) and BGRA (4) inputs keep their channel count
        assert result.shape == image.shape


def test_no_detections_returns_unchanged():
    """Image with no faces/smiles should return the original image unchanged."""
    image = make_blank_image(channels=3)
    op = make_operator({})

    result = op.compute(image.copy())

    # For blank images with no detections, output should match input
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
    # 5-channel image is not supported
    image = np.zeros((100, 100, 5), dtype=np.uint8)
    op = make_operator({})
    
    with pytest.raises(ValueError, match="Unsupported image shape"):
        op.compute(image)


def test_grayscale_2d_image():
    """2D grayscale images (H, W) should be processed correctly."""
    image = make_blank_image(channels=1).squeeze()
    assert len(image.shape) == 2  # Ensure it's 2D
    
    op = make_operator({})
    result = op.compute(image.copy())
    
    # Output should be BGR (3 channels) for colored boxes
    assert result.shape == (200, 200, 3)
    assert result.dtype == np.uint8


def test_cascade_initialization():
    """Operator should successfully load Haar cascade files."""
    # If cascade files are missing or paths are wrong, __init__ should raise
    try:
        op = make_operator({})
        # If we reach here, cascades loaded successfully
        assert not op.face_cascade.empty()
        assert not op.smile_cascade.empty()
    except ValueError as e:
        pytest.fail(f"Cascade initialization failed: {e}")


def test_different_box_colors():
    """Different box colors should be accepted without error."""
    colors = ["#FF0000", "#00FF00", "#0000FF", "#FFFF00"]
    image = make_blank_image(channels=3)
    
    for color in colors:
        op = make_operator({"rgbcolors_input": color})
        result = op.compute(image.copy())
        assert result.shape == image.shape


def test_draw_face_boxes_parameter():
    """drawFaceBoxes parameter should be accepted (True/False)."""
    image = make_blank_image(channels=3)
    
    # Test with False (default)
    op_false = make_operator({"drawFaceBoxes": False})
    result_false = op_false.compute(image.copy())
    assert result_false.shape == image.shape
    
    # Test with True
    op_true = make_operator({"drawFaceBoxes": True})
    result_true = op_true.compute(image.copy())
    assert result_true.shape == image.shape


def test_float_images_normalized():
    """Float images in [0, 1] range should be handled correctly."""
    # Create float image in [0, 1] range
    image = np.ones((100, 100, 3), dtype=np.float32) * 0.5
    op = make_operator({})
    
    result = op.compute(image.copy())
    
    # Result should be uint8
    assert result.dtype == np.uint8
    assert result.shape == (100, 100, 3)


def test_uint16_images_converted():
    """uint16 images should be converted to uint8 correctly."""
    # Create uint16 image
    image = np.ones((100, 100, 3), dtype=np.uint16) * 32768
    op = make_operator({})
    
    result = op.compute(image.copy())
    
    # Result should be uint8
    assert result.dtype == np.uint8
    assert result.shape == (100, 100, 3)

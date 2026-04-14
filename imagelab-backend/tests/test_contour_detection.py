import cv2
import numpy as np
import pytest

from app.operators.filtering.contour_detection import ContourDetection


def test_contour_detection_no_contours():
    operator = ContourDetection({"mode": "EXTERNAL", "method": "SIMPLE", "rgbcolors_input": "#00ff00", "thickness": 2})
    blank_image = np.zeros((100, 100, 3), dtype=np.uint8)
    result = operator.compute(blank_image)
    # Shape must be consistent regardless of whether contours were found
    assert result.shape == blank_image.shape
    assert np.array_equal(result, blank_image)


def test_contour_detection_grayscale_input():
    # Test that grayscale input converts to BGR and draws contours
    operator = ContourDetection({"mode": "TREE", "method": "NONE", "rgbcolors_input": "#ff0000", "thickness": 1})
    test_image = np.zeros((50, 50), dtype=np.uint8)
    cv2.rectangle(test_image, (10, 10), (40, 40), 255, -1)

    result = operator.compute(test_image.copy())

    assert result.ndim == 3
    assert result.shape[2] == 3

    # Check that output has changed (pixels drawn) and contains red pixels
    assert not np.array_equal(result, cv2.cvtColor(test_image, cv2.COLOR_GRAY2BGR))
    assert np.any(result[:, :, 2] == 255)  # Red channel (BGR index 2)


def test_contour_detection_grayscale_no_contours_shape_consistent():
    # Even with no contours, grayscale input must return a BGR image (consistent shape)
    operator = ContourDetection({"mode": "EXTERNAL", "method": "SIMPLE", "rgbcolors_input": "#00ff00", "thickness": 2})
    blank_gray = np.zeros((50, 50), dtype=np.uint8)
    result = operator.compute(blank_gray)
    assert result.ndim == 3
    assert result.shape[2] == 3


def test_contour_detection_bgra_input():
    # Test that BGRA input draws properly without crashing and retains alpha
    operator = ContourDetection({"mode": "EXTERNAL", "method": "SIMPLE", "rgbcolors_input": "#00ff00", "thickness": 2})
    test_image = np.zeros((50, 50, 4), dtype=np.uint8)
    test_image[:, :, 3] = 255
    cv2.rectangle(test_image, (10, 10), (40, 40), (255, 255, 255, 255), -1)

    result = operator.compute(test_image.copy())

    assert result.shape == test_image.shape
    # Check that green pixels were drawn (hex #00ff00 -> BGR index 1)
    assert np.any(result[:, :, 1] == 255)
    # Alpha channel should remain intact
    assert np.all(result[:, :, 3] == 255)


def test_contour_detection_float_image_normalized():
    # CRITICAL regression: float [0,1] images must not be silently destroyed
    operator = ContourDetection({"mode": "EXTERNAL", "method": "SIMPLE", "rgbcolors_input": "#00ff00", "thickness": 2})
    test_image = np.zeros((50, 50, 3), dtype=np.float32)
    # Draw a bright rectangle in float range [0.0, 1.0]
    test_image[10:40, 10:40] = 1.0

    result = operator.compute(test_image.copy())

    # Must find contours and draw; result should contain green pixels
    assert result.shape[2] == 3
    # Green channel (BGR index 1) should have drawn pixels
    assert np.any(result[:, :, 1] > 0)


def test_contour_detection_invalid_mode_raises():
    operator = ContourDetection({"mode": "INVALID", "method": "SIMPLE", "rgbcolors_input": "#00ff00", "thickness": 2})
    image = np.zeros((50, 50, 3), dtype=np.uint8)
    with pytest.raises(ValueError, match="Invalid contour mode"):
        operator.compute(image)


def test_contour_detection_invalid_method_raises():
    operator = ContourDetection({"mode": "EXTERNAL", "method": "INVALID", "rgbcolors_input": "#00ff00", "thickness": 2})
    image = np.zeros((50, 50, 3), dtype=np.uint8)
    with pytest.raises(ValueError, match="Invalid contour method"):
        operator.compute(image)


def test_contour_detection_invalid_thickness_raises():
    operator = ContourDetection({"mode": "EXTERNAL", "method": "SIMPLE", "rgbcolors_input": "#00ff00", "thickness": 0})
    image = np.zeros((50, 50, 3), dtype=np.uint8)
    with pytest.raises(ValueError, match="thickness must be between 1 and 50"):
        operator.compute(image)


def test_contour_detection_thickness_too_large_raises():
    operator = ContourDetection({"mode": "EXTERNAL", "method": "SIMPLE", "rgbcolors_input": "#00ff00", "thickness": 51})
    image = np.zeros((50, 50, 3), dtype=np.uint8)
    with pytest.raises(ValueError, match="thickness must be between 1 and 50"):
        operator.compute(image)

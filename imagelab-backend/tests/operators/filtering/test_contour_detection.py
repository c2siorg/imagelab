"""Tests for the contour detection operator."""

import numpy as np
import pytest

from app.operators.filtering.contour_detection import ContourDetection


def make_operator(params: dict):
    """Create a ContourDetection operator with params."""
    return ContourDetection(params or {})


def make_rect_image(channels=3, bg=0, fg=255):
    """Create a simple synthetic image with a centered rectangle."""
    if channels == 1:
        image = np.full((100, 100), bg, dtype=np.uint8)
        image[30:70, 30:70] = fg
        return image
    image = np.full((100, 100, channels), bg, dtype=np.uint8)
    image[30:70, 30:70] = fg
    return image


@pytest.mark.parametrize(
    "params",
    [
        {},  # defaults
        {"rgbcolors_input": "#00FF00", "thickness": 1, "mode": "EXTERNAL", "method": "SIMPLE"},
        {"rgbcolors_input": "#FF0000", "thickness": 2, "mode": "TREE", "method": "NONE"},
    ],
)
def test_contour_detection_returns_valid_image(params):
    """Operator should return an image with same shape and dtype."""
    image = make_rect_image(channels=3, bg=0, fg=255)
    op = make_operator(params)

    result = op.compute(image.copy())

    assert result.shape == image.shape
    assert result.dtype == image.dtype


@pytest.mark.parametrize("channels", [1, 3, 4])
def test_contour_detection_supports_gray_bgr_bgra(channels):
    """Operator should process grayscale, BGR, and BGRA inputs."""
    image = make_rect_image(channels=channels, bg=0, fg=255)
    op = make_operator({})

    result = op.compute(image.copy())

    if channels == 1:
        assert result.shape == (100, 100, 3)  # grayscale -> BGR conversion for drawing
    elif channels == 4:
        assert result.shape == (100, 100, 4)  # BGRA preserved, alpha retained
    else:
        assert result.shape == image.shape


def test_does_not_mutate_input():
    image = np.zeros((100, 100, 3), dtype=np.uint8)
    original = image.copy()
    op = make_operator({})
    _ = op.compute(image)
    np.testing.assert_array_equal(image, original)

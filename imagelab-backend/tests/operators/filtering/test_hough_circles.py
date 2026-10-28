"""Tests for the Hough circle detection operator."""

import ast

import cv2
import numpy as np
import pytest

from app.models.pipeline import PipelineStep
from app.operators.filtering.hough_circles import HoughCircles
from app.operators.registry import get_operator
from app.services.python_exporter.generator import export_pipeline_to_python

GREEN = "#00ff00"
GREEN_BGR = (0, 255, 0)
RED = "#ff0000"
RED_BGR = (0, 0, 255)
BLUE = "#0000ff"
BLUE_BGR = (255, 0, 0)


def make_operator(params: dict | None = None) -> HoughCircles:
    """Create a HoughCircles operator with given parameters."""
    return HoughCircles(params or {})


def make_circle_image(
    center=(100, 100),
    radius=40,
    channels=3,
    bg=0,
    fg=255,
    thickness=2,
    size=(200, 200),
) -> np.ndarray:
    """Create a synthetic image with a solid or outlined circle."""
    if channels == 1:
        img = np.full(size, bg, dtype=np.uint8)
        cv2.circle(img, center, radius, fg, thickness)
        return img
    img = np.full((size[0], size[1], channels), bg, dtype=np.uint8)
    color = (fg,) * channels
    cv2.circle(img, center, radius, color, thickness)
    return img


def test_registered_in_registry():
    assert get_operator("filtering_houghcircles") is HoughCircles


def test_circle_detected_and_drawn_in_bgr():
    """Synthetic circle should be detected and marked on a BGR image."""
    img = make_circle_image(center=(100, 100), radius=40, channels=3, thickness=2)
    params = {
        "dp": 1.0,
        "minDist": 50,
        "param1": 100,
        "param2": 25,
        "minRadius": 30,
        "maxRadius": 50,
        "circleColor": GREEN,
        "thickness": 2,
        "drawCenters": True,
        "centerColor": RED,
        "centerRadius": 3,
    }
    result = make_operator(params).compute(img)
    assert result.shape == img.shape
    assert result.dtype == np.uint8

    # Assert green circle pixels exist
    green_mask = np.all(result == GREEN_BGR, axis=-1)
    green_pixels = np.nonzero(green_mask)
    assert len(green_pixels[0]) > 0

    # Assert center dot exists near (100, 100)
    red_mask = np.all(result == RED_BGR, axis=-1)
    red_pixels = np.nonzero(red_mask)
    assert len(red_pixels[0]) > 0
    center_y_mean = np.mean(red_pixels[0])
    center_x_mean = np.mean(red_pixels[1])
    assert abs(center_x_mean - 100) <= 5
    assert abs(center_y_mean - 100) <= 5


def test_grayscale_image_promoted_to_bgr_canvas():
    """Grayscale inputs should be promoted to 3-channel BGR so colored annotations show."""
    gray = make_circle_image(center=(80, 80), radius=35, channels=1, thickness=2)
    params = {
        "dp": 1.0,
        "minDist": 40,
        "param1": 100,
        "param2": 25,
        "minRadius": 25,
        "maxRadius": 45,
        "circleColor": BLUE,
        "thickness": 2,
    }
    result = make_operator(params).compute(gray)
    assert result.shape == (200, 200, 3)
    assert result.dtype == np.uint8

    blue_mask = np.all(result == BLUE_BGR, axis=-1)
    assert np.any(blue_mask)


def test_grayscale_3d_single_channel_promoted_to_bgr():
    """(H, W, 1) image should also be converted to 3-channel BGR."""
    gray_3d = make_circle_image(center=(80, 80), radius=35, channels=1, thickness=2)[:, :, np.newaxis]
    result = make_operator().compute(gray_3d)
    assert result.shape == (200, 200, 3)


def test_bgra_image_preserves_alpha_channel():
    """BGRA images must retain 4 channels and original alpha values outside drawn pixels."""
    bgr = make_circle_image(center=(100, 100), radius=40, channels=3, thickness=2)
    alpha = np.full((200, 200), 128, dtype=np.uint8)
    bgra = np.dstack([bgr, alpha])

    params = {
        "dp": 1.0,
        "minDist": 50,
        "param1": 100,
        "param2": 25,
        "minRadius": 30,
        "maxRadius": 50,
        "circleColor": GREEN,
        "thickness": 2,
    }
    result = make_operator(params).compute(bgra)
    assert result.shape == (200, 200, 4)
    assert result.dtype == np.uint8

    # Check drawn pixels have full opacity (alpha = 255)
    green_drawn_mask = np.all(result[:, :, :3] == GREEN_BGR, axis=-1)
    assert np.any(green_drawn_mask)
    np.testing.assert_array_equal(result[green_drawn_mask, 3], 255)

    # Undrawn pixels keep alpha = 128
    undrawn_mask = ~green_drawn_mask & ~np.all(result[:, :, :3] == RED_BGR, axis=-1)
    np.testing.assert_array_equal(result[undrawn_mask, 3], 128)


def test_no_circles_detected_returns_canvas_unchanged():
    """An image without circles returns unchanged pixels."""
    flat = np.full((100, 100, 3), 100, dtype=np.uint8)
    result = make_operator({"param2": 100}).compute(flat)
    np.testing.assert_array_equal(result, flat)


def test_no_circles_grayscale_promotes_canvas_cleanly():
    """A grayscale image with no circles returns a 3-channel grayscale BGR image."""
    flat_gray = np.full((100, 100), 100, dtype=np.uint8)
    result = make_operator({"param2": 100}).compute(flat_gray)
    assert result.shape == (100, 100, 3)
    np.testing.assert_array_equal(result[:, :, 0], 100)
    np.testing.assert_array_equal(result[:, :, 1], 100)
    np.testing.assert_array_equal(result[:, :, 2], 100)


def test_draw_centers_flag_disabled():
    """When drawCenters is False, center color markers must not be drawn."""
    img = make_circle_image(center=(100, 100), radius=40, channels=3, thickness=2)
    params = {
        "dp": 1.0,
        "minDist": 50,
        "param1": 100,
        "param2": 25,
        "minRadius": 30,
        "maxRadius": 50,
        "circleColor": GREEN,
        "drawCenters": False,
        "centerColor": RED,
    }
    result = make_operator(params).compute(img)
    # Circle outline exists
    assert np.any(np.all(result == GREEN_BGR, axis=-1))
    # Red center does not exist
    assert not np.any(np.all(result == RED_BGR, axis=-1))


def test_invalid_empty_or_none_image():
    with pytest.raises(ValueError, match="received an invalid or empty image"):
        make_operator().compute(None)

    with pytest.raises(ValueError, match="received an invalid or empty image"):
        make_operator().compute(np.array([], dtype=np.uint8))


def test_parameter_bounds_validation():
    img = np.zeros((50, 50, 3), dtype=np.uint8)

    with pytest.raises(ValueError, match="dp must be between"):
        make_operator({"dp": 0.1}).compute(img)

    with pytest.raises(ValueError, match="minDist must be between"):
        make_operator({"minDist": 0.0}).compute(img)

    with pytest.raises(ValueError, match="param1 must be between"):
        make_operator({"param1": 0.0}).compute(img)

    with pytest.raises(ValueError, match="param2 must be between"):
        make_operator({"param2": 0.0}).compute(img)

    with pytest.raises(ValueError, match="minRadius must be between"):
        make_operator({"minRadius": -1}).compute(img)

    with pytest.raises(ValueError, match="maxRadius must be between"):
        make_operator({"maxRadius": -1}).compute(img)

    with pytest.raises(ValueError, match="cannot be greater than maxRadius"):
        make_operator({"minRadius": 50, "maxRadius": 30}).compute(img)

    with pytest.raises(ValueError, match="thickness must be between"):
        make_operator({"thickness": 0}).compute(img)

    with pytest.raises(ValueError, match="centerRadius must be between"):
        make_operator({"centerRadius": 0}).compute(img)


def test_exporter_template_ast_and_execution():
    """Verify exported python script for HoughCircles generates valid AST and produces identical output."""
    img = make_circle_image(center=(100, 100), radius=40, channels=3, thickness=2)
    step = PipelineStep(
        type="filtering_houghcircles",
        params={
            "dp": 1.0,
            "minDist": 50,
            "param1": 100,
            "param2": 25,
            "minRadius": 30,
            "maxRadius": 50,
            "circleColor": "#00ff00",
            "thickness": 2,
            "drawCenters": True,
            "centerColor": "#ff0000",
            "centerRadius": 3,
        },
    )

    code, unsupported = export_pipeline_to_python([step], "Hough Circle Test")
    assert unsupported == []
    assert "cv2.HoughCircles" in code

    # Validate AST
    tree = ast.parse(code)
    assert isinstance(tree, ast.Module)

    # Compile bytecode
    compiled = compile(tree, filename="test_hough_script.py", mode="exec")

    # Execute in clean namespace
    namespace = {}
    exec(compiled, namespace)
    assert "run_pipeline" in namespace

    exported_result = namespace["run_pipeline"](img.copy())
    operator_result = make_operator(step.params).compute(img.copy())

    np.testing.assert_array_equal(exported_result, operator_result)

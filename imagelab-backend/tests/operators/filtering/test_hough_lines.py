"""Tests for the Hough line detection operator."""

import cv2
import numpy as np
import pytest

from app.operators.filtering.hough_lines import HoughLines
from app.operators.registry import get_operator

RED = "#ff0000"
RED_BGR = (0, 0, 255)


def make_operator(params: dict | None = None):
    """Create a HoughLines operator with params."""
    return HoughLines(params or {})


def make_line_image(start, end, channels=3, bg=0):
    """Create a 200x200 image with a 3px wide white line from start to end.

    A 3px line produces a strong, 160px long Canny edge on each side, far above
    the default threshold (50) and minLineLength (50), so HoughLinesP always
    returns at least one segment regardless of OpenCV build.
    """
    if channels == 1:
        image = np.full((200, 200), bg, dtype=np.uint8)
        cv2.line(image, start, end, 255, 3)
        return image
    image = np.full((200, 200, channels), bg, dtype=np.uint8)
    white = (255,) * channels
    cv2.line(image, start, end, white, 3)
    return image


def red_pixels(result: np.ndarray):
    """Return (rows, cols) of pixels painted in the test colour."""
    mask = np.all(result[:, :, :3] == RED_BGR, axis=-1)
    return np.nonzero(mask)


def test_registered_in_registry():
    assert get_operator("filtering_houghlines") is HoughLines


def test_horizontal_line_is_drawn_at_its_position():
    """A horizontal line must produce red segments within a few px of row 100."""
    image = make_line_image((20, 100), (180, 100))
    result = make_operator({"color": RED, "thickness": 1}).compute(image)

    rows, cols = red_pixels(result)
    assert len(rows) > 0
    assert rows.min() >= 95 and rows.max() <= 105
    assert cols.min() >= 15 and cols.max() <= 185
    # The segment spans most of the line, not just a short fragment
    assert cols.max() - cols.min() >= 120


def test_vertical_line_is_drawn_at_its_position():
    """A vertical line must produce red segments within a few px of column 60."""
    image = make_line_image((60, 20), (60, 180))
    result = make_operator({"color": RED, "thickness": 1}).compute(image)

    rows, cols = red_pixels(result)
    assert len(rows) > 0
    assert cols.min() >= 55 and cols.max() <= 65
    assert rows.min() >= 15 and rows.max() <= 185
    assert rows.max() - rows.min() >= 120


def test_diagonal_line_is_drawn_along_its_angle():
    """Every drawn pixel on a 45 degree line must satisfy y ~= x."""
    image = make_line_image((20, 20), (180, 180))
    result = make_operator({"color": RED, "thickness": 1}).compute(image)

    rows, cols = red_pixels(result)
    assert len(rows) > 0
    assert np.abs(rows - cols).max() <= 6


def test_segments_are_drawn_on_original_image_not_edge_map():
    """Background pixels must keep the source colour instead of becoming black."""
    bg_bgr = (200, 50, 50)
    image = np.full((200, 200, 3), bg_bgr, dtype=np.uint8)
    cv2.line(image, (20, 100), (180, 100), (255, 255, 255), 3)

    result = make_operator({"color": RED}).compute(image)

    assert result.shape == image.shape
    assert tuple(result[10, 10]) == bg_bgr
    assert tuple(result[190, 190]) == bg_bgr
    assert len(red_pixels(result)[0]) > 0


def test_blank_image_is_returned_unchanged():
    image = np.full((100, 100, 3), 128, dtype=np.uint8)
    result = make_operator({}).compute(image)

    assert np.array_equal(result, image)
    assert result is not image


def test_input_image_is_not_mutated():
    image = make_line_image((20, 100), (180, 100))
    original = image.copy()

    make_operator({"color": RED}).compute(image)

    assert np.array_equal(image, original)


def test_grayscale_input_is_promoted_to_bgr_and_drawn_in_colour():
    image = make_line_image((20, 100), (180, 100), channels=1)
    result = make_operator({"color": RED, "thickness": 1}).compute(image)

    assert result.ndim == 3 and result.shape[2] == 3
    rows, _ = red_pixels(result)
    assert len(rows) > 0
    assert rows.min() >= 95 and rows.max() <= 105


def test_blank_grayscale_input_keeps_consistent_bgr_output():
    """Output channel count must not depend on whether any lines were found."""
    image = np.full((100, 100), 128, dtype=np.uint8)
    result = make_operator({}).compute(image)

    assert result.shape == (100, 100, 3)
    for channel in range(3):
        assert np.array_equal(result[:, :, channel], image)


def test_bgra_input_keeps_alpha_and_draws_opaque_lines():
    image = make_line_image((20, 100), (180, 100), channels=4)
    image[:, :, 3] = 255
    result = make_operator({"color": RED, "thickness": 1}).compute(image)

    assert result.shape == image.shape
    assert result[:, :, 3].min() == 255
    rows, _ = red_pixels(result)
    assert len(rows) > 0


def test_float_input_in_unit_range_is_detected():
    image = make_line_image((20, 100), (180, 100)).astype(np.float32) / 255.0
    result = make_operator({"color": RED, "thickness": 1}).compute(image)

    assert result.dtype == np.float32
    mask = np.all(result == (0.0, 0.0, 255.0), axis=-1)
    assert mask.any()


def test_thickness_controls_drawn_width():
    image = make_line_image((20, 100), (180, 100))
    thin = make_operator({"color": RED, "thickness": 1}).compute(image)
    thick = make_operator({"color": RED, "thickness": 5}).compute(image)

    assert len(red_pixels(thick)[0]) > len(red_pixels(thin)[0])


def test_colour_is_parsed_from_hex():
    image = make_line_image((20, 100), (180, 100))
    result = make_operator({"color": "#0000ff", "thickness": 1}).compute(image)

    blue = np.all(result == (255, 0, 0), axis=-1)
    assert blue.any()
    assert not np.all(result == RED_BGR, axis=-1).any()


def test_parameters_are_forwarded_to_houghlinesp(monkeypatch):
    """thetaDegrees is converted to radians and the edge map, not the image, is searched."""
    captured = {}

    def fake_hough_lines_p(edges, rho, theta, threshold, minLineLength, maxLineGap):
        captured.update(
            edges=edges,
            rho=rho,
            theta=theta,
            threshold=threshold,
            minLineLength=minLineLength,
            maxLineGap=maxLineGap,
        )
        return None

    monkeypatch.setattr("app.operators.filtering.hough_lines.cv2.HoughLinesP", fake_hough_lines_p)

    image = make_line_image((20, 100), (180, 100))
    params = {"rho": 2.0, "thetaDegrees": 90.0, "threshold": 80, "minLineLength": 30, "maxLineGap": 5}
    result = make_operator(params).compute(image)

    assert captured["rho"] == 2.0
    assert captured["theta"] == pytest.approx(np.pi / 2)
    assert captured["threshold"] == 80
    assert captured["minLineLength"] == 30
    assert captured["maxLineGap"] == 5
    # Canny output is a single-channel binary map
    assert captured["edges"].ndim == 2
    assert set(np.unique(captured["edges"])) <= {0, 255}
    # None from HoughLinesP leaves the image untouched
    assert np.array_equal(result, image)


def test_high_threshold_finds_no_lines_and_returns_input():
    image = make_line_image((20, 100), (180, 100))
    result = make_operator({"color": RED, "threshold": 1000, "minLineLength": 10000}).compute(image)

    assert np.array_equal(result, image)


@pytest.mark.parametrize(
    ("params", "message"),
    [
        ({"rho": 0}, "rho must be between 0.1 and 10"),
        ({"rho": -1}, "rho must be between 0.1 and 10"),
        ({"rho": 11}, "rho must be between 0.1 and 10"),
        ({"thetaDegrees": 0}, "thetaDegrees must be between 0.1 and 180"),
        ({"thetaDegrees": 181}, "thetaDegrees must be between 0.1 and 180"),
        ({"threshold": 0}, "threshold must be between 1 and 1000"),
        ({"threshold": 1001}, "threshold must be between 1 and 1000"),
        ({"minLineLength": -1}, "minLineLength must be between 0 and 10000"),
        ({"minLineLength": 10001}, "minLineLength must be between 0 and 10000"),
        ({"maxLineGap": -1}, "maxLineGap must be between 0 and 10000"),
        ({"maxLineGap": 10001}, "maxLineGap must be between 0 and 10000"),
        ({"thickness": 0}, "thickness must be between 1 and 50"),
        ({"thickness": 51}, "thickness must be between 1 and 50"),
    ],
)
def test_invalid_parameters_raise(params, message):
    image = make_line_image((20, 100), (180, 100))
    with pytest.raises(ValueError, match=message):
        make_operator(params).compute(image)


def test_invalid_colour_raises():
    image = make_line_image((20, 100), (180, 100))
    with pytest.raises(ValueError, match="Invalid hex color"):
        make_operator({"color": "red"}).compute(image)


def test_unsupported_shape_raises():
    image = np.zeros((10, 10, 2), dtype=np.uint8)
    with pytest.raises(ValueError, match="Unsupported image shape"):
        make_operator({}).compute(image)


def test_runs_through_pipeline_executor(client, sample_image_b64):
    """The operator is reachable from the API by its registered block type."""
    response = client.post(
        "/api/v1/pipeline/executions",
        json={
            "image": sample_image_b64,
            "image_format": "png",
            "pipeline": [{"type": "filtering_houghlines", "block_id": "hough", "params": {"color": RED}}],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["timings"]["steps"][0]["operator_type"] == "filtering_houghlines"

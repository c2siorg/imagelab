import numpy as np
import pytest

from app.operators.drawing.draw_ellipse import DrawEllipse


def test_wide_ellipse_spans_more_horizontally() -> None:
    """A wide ellipse (width > height) must span further on the x-axis than y-axis."""
    img = np.zeros((200, 200, 3), dtype=np.uint8)
    params = {
        "center_point_x": 100,
        "center_point_y": 100,
        "width": 80,
        "height": 30,
        "angle": 0,
        "rgbcolors_input": "#ffffff",
    }
    out = DrawEllipse(params).compute(img)
    ys, xs = np.where(np.any(out > 0, axis=2))
    assert int(xs.max() - xs.min()) > int(ys.max() - ys.min()), (
        "Expected a wide (landscape) ellipse but got a tall one — axes may be swapped"
    )


def test_tall_ellipse_spans_more_vertically() -> None:
    """A tall ellipse (height > width) must span further on the y-axis than x-axis."""
    img = np.zeros((200, 200, 3), dtype=np.uint8)
    params = {
        "center_point_x": 100,
        "center_point_y": 100,
        "width": 30,
        "height": 80,
        "angle": 0,
        "rgbcolors_input": "#ffffff",
    }
    out = DrawEllipse(params).compute(img)
    ys, xs = np.where(np.any(out > 0, axis=2))
    assert int(ys.max() - ys.min()) > int(xs.max() - xs.min()), (
        "Expected a tall (portrait) ellipse but got a wide one — axes may be swapped"
    )


def test_ellipse_preserves_shape() -> None:
    """Output image must have the same dimensions as input."""
    img = np.zeros((100, 150, 3), dtype=np.uint8)
    params = {"center_point_x": 75, "center_point_y": 50, "width": 40, "height": 20, "angle": 0}
    out = DrawEllipse(params).compute(img)
    assert out.shape == img.shape


def test_circle_is_symmetric() -> None:
    """When width == height the ellipse is a circle and x/y span should be equal."""
    img = np.zeros((200, 200, 3), dtype=np.uint8)
    params = {
        "center_point_x": 100,
        "center_point_y": 100,
        "width": 60,
        "height": 60,
        "angle": 0,
        "rgbcolors_input": "#ffffff",
    }
    out = DrawEllipse(params).compute(img)
    ys, xs = np.where(np.any(out > 0, axis=2))
    x_span = int(xs.max() - xs.min())
    y_span = int(ys.max() - ys.min())
    TOLERANCE = 2
    assert abs(x_span - y_span) <= TOLERANCE, (
        f"Circle x_span={x_span}, y_span={y_span} differ by more than {TOLERANCE} px"
    )


def test_angle_rotates_ellipse() -> None:
    """A 90-degree rotation of a non-square ellipse swaps the dominant axis."""
    img = np.zeros((200, 200, 3), dtype=np.uint8)
    base = {"center_point_x": 100, "center_point_y": 100, "width": 80, "height": 30, "rgbcolors_input": "#ffffff"}
    out0 = DrawEllipse({**base, "angle": 0}).compute(img.copy())
    out90 = DrawEllipse({**base, "angle": 90}).compute(img.copy())
    ys0, xs0 = np.where(np.any(out0 > 0, axis=2))
    ys90, xs90 = np.where(np.any(out90 > 0, axis=2))
    assert (xs0.max() - xs0.min()) == pytest.approx(ys90.max() - ys90.min(), abs=4)


def test_defaults_do_not_raise() -> None:
    """DrawEllipse with an empty params dict should not raise an exception."""
    img = np.zeros((200, 200, 3), dtype=np.uint8)
    DrawEllipse({}).compute(img)


@pytest.mark.parametrize(
    ("width", "height"),
    [
        (-10, 20),
        (20, -10),
        (-50, -50),
    ],
)
def test_negative_dimensions_clamped_without_crash(width: int, height: int) -> None:
    """Negative semi-axes dimensions must be clamped to 0 without raising cv2.error."""
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    params = {"center_point_x": 50, "center_point_y": 50, "width": width, "height": height}
    out = DrawEllipse(params).compute(img)
    assert out.shape == img.shape
    assert out.dtype == np.uint8


@pytest.mark.parametrize("thickness", [0, -2, -10])
def test_invalid_thickness_clamped_without_crash(thickness: int) -> None:
    """Invalid thickness values (0 or < -1) must be clamped to at least 1 without cv2.error."""
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    params = {"center_point_x": 50, "center_point_y": 50, "width": 30, "height": 20, "thickness": thickness}
    out = DrawEllipse(params).compute(img)
    assert out.shape == img.shape
    assert out.dtype == np.uint8


def test_filled_ellipse_thickness_minus_one() -> None:
    """thickness=-1 is cv2.FILLED and should fill the ellipse interior."""
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    params = {
        "center_point_x": 50,
        "center_point_y": 50,
        "width": 30,
        "height": 20,
        "thickness": -1,
        "rgbcolors_input": "#ffffff",
    }
    out = DrawEllipse(params).compute(img)
    # The center of the filled ellipse should be drawn with color #ffffff (255, 255, 255)
    assert np.all(out[50, 50] == 255)


def test_non_integer_parameters_handled_gracefully() -> None:
    """Non-integer/corrupt params should fall back to safe defaults without crashing."""
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    params = {
        "center_point_x": "bad",
        "center_point_y": None,
        "width": "invalid",
        "height": None,
        "thickness": "none",
        "angle": "abc",
    }
    out = DrawEllipse(params).compute(img)
    assert out.shape == img.shape
    assert out.dtype == np.uint8

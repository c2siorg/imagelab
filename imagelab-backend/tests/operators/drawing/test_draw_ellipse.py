import numpy as np

from app.operators.drawing.draw_ellipse import DrawEllipse


def test_wide_ellipse_spans_more_horizontally() -> None:
    """A wide ellipse (width > height) must span further on the x-axis than y-axis."""
    img = np.zeros((200, 200, 3), dtype=np.uint8)
    params = {"center_point_x": 100, "center_point_y": 100, "width": 80, "height": 30, "angle": 0}
    out = DrawEllipse(params).compute(img)
    ys, xs = np.where(out[:, :, 0] > 0)
    assert int(xs.max() - xs.min()) > int(ys.max() - ys.min()), (
        "Expected a wide (landscape) ellipse but got a tall one — axes may be swapped"
    )


def test_tall_ellipse_spans_more_vertically() -> None:
    """A tall ellipse (height > width) must span further on the y-axis than x-axis."""
    img = np.zeros((200, 200, 3), dtype=np.uint8)
    params = {"center_point_x": 100, "center_point_y": 100, "width": 30, "height": 80, "angle": 0}
    out = DrawEllipse(params).compute(img)
    ys, xs = np.where(out[:, :, 0] > 0)
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
    params = {"center_point_x": 100, "center_point_y": 100, "width": 60, "height": 60, "angle": 0}
    out = DrawEllipse(params).compute(img)
    ys, xs = np.where(out[:, :, 0] > 0)
    x_span = int(xs.max() - xs.min())
    y_span = int(ys.max() - ys.min())
    assert abs(x_span - y_span) <= 4, f"Circle x_span={x_span}, y_span={y_span} differ too much"

import numpy as np
import pytest

from app.operators.geometric.rotate_image import RotateImage


def _expected_rotated_xy(x: int, y: int, cx: float, cy: float, angle_deg: float) -> tuple:
    a = angle_deg % 360
    if a == 0:
        return (x, y)
    if a == 90:
        return (int(round(cx + (y - cy))), int(round(cy - (x - cx))))
    if a == 180:
        return (int(round(cx - (x - cx))), int(round(cy - (y - cy))))
    if a == 270:
        return (int(round(cx - (y - cy))), int(round(cy + (x - cx))))
    raise ValueError("This helper is only for 0/90/180/270.")


@pytest.mark.parametrize("angle", [0, 90, 180, 270])
def test_rotate_preserves_shape(angle: int) -> None:
    img = np.zeros((200, 200), dtype=np.uint8)
    out = RotateImage({"angle": angle, "scale": 1.0}).compute(img)
    assert out.shape == img.shape


def test_rotate_0_is_identity() -> None:
    img = np.random.randint(0, 256, size=(120, 160), dtype=np.uint8)
    out = RotateImage({"angle": 0, "scale": 1.0}).compute(img)
    assert np.array_equal(out, img)


@pytest.mark.parametrize("angle", [90, 180, 270])
def test_rotate_moves_sentinel_pixel_to_expected_location(angle: int) -> None:
    h, w = 200, 200
    img = np.zeros((h, w), dtype=np.uint8)
    x0, y0 = 90, 80
    img[y0, x0] = 255
    out = RotateImage({"angle": angle, "scale": 1.0}).compute(img)
    cx, cy = w / 2, h / 2
    x1, y1 = _expected_rotated_xy(x0, y0, cx, cy, float(angle))
    assert out.max() > 0
    y_got, x_got = np.unravel_index(out.argmax(), out.shape)
    assert (int(x_got), int(y_got)) == (x1, y1)

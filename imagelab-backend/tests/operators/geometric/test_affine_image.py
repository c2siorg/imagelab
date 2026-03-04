import numpy as np
import pytest

from app.operators.geometric.affine_image import AffineImage

# explicit translation contract — all tests use the same dx/dy
_DX, _DY = 50, 100


def test_affine_preserves_shape() -> None:
    img = np.zeros((240, 320), dtype=np.uint8)
    out = AffineImage({"dx": _DX, "dy": _DY}).compute(img)
    assert out.shape == img.shape


@pytest.mark.parametrize(
    "src_xy,expected_xy",
    [
        ((10, 10), (60, 110)),
        ((0, 0), (50, 100)),
        ((100, 50), (150, 150)),
        ((200, 10), (250, 110)),
    ],
)
def test_affine_translates_sentinel_pixel_when_in_bounds(src_xy: tuple[int, int], expected_xy: tuple[int, int]) -> None:
    h, w = 300, 300
    img = np.zeros((h, w), dtype=np.uint8)
    x0, y0 = src_xy
    x1, y1 = expected_xy
    img[y0, x0] = 255
    out = AffineImage({"dx": _DX, "dy": _DY}).compute(img)
    # integer translation hits exact grid points — no interpolation blending
    assert out[y1, x1] == 255
    assert out.max() == 255


@pytest.mark.parametrize(
    "shape,src_xy",
    [
        ((120, 120), (80, 80)),
        ((140, 60), (10, 10)),
    ],
)
def test_affine_pixel_can_shift_out_of_bounds(shape: tuple[int, int], src_xy: tuple[int, int]) -> None:
    h, w = shape
    img = np.zeros((h, w), dtype=np.uint8)
    x0, y0 = src_xy
    img[y0, x0] = 255
    out = AffineImage({"dx": _DX, "dy": _DY}).compute(img)
    # AffineImage uses BORDER_CONSTANT(0); pixels shifted out of bounds become 0
    assert out.max() == 0

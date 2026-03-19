import numpy as np
import pytest

from app.operators.geometric.scale_image import ScaleImage


@pytest.mark.parametrize("interp", ["LINEAR", "AREA", "CUBIC", "NEAREST", "LANCZOS4"])
def test_scale_image_interpolation_modes(interp):
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    op = ScaleImage(params={"fx": 1.5, "fy": 1.5, "interpolation": interp})
    result = op.compute(img)
    assert result.shape == (150, 150, 3)


def test_scale_image_default_interpolation():
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    op = ScaleImage(params={"fx": 2, "fy": 2})
    result = op.compute(img)
    assert result.shape == (200, 200, 3)


def test_scale_image_interpolation_case_insensitive():
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    op = ScaleImage(params={"fx": 1, "fy": 1, "interpolation": "linear"})
    result = op.compute(img)
    assert result.shape == (100, 100, 3)


def test_scale_image_invalid_interpolation_raises():
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    op = ScaleImage(params={"fx": 1, "fy": 1, "interpolation": "BICUBIC"})
    with pytest.raises(ValueError, match="Unknown interpolation"):
        op.compute(img)

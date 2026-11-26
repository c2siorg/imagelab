import numpy as np
import pytest

from app.operators.conversions.clahe import ClaheImage


def make_op(params=None):
    return ClaheImage(params or {})


def test_grayscale():
    img = np.random.randint(0, 256, (64, 64), dtype=np.uint8)
    result = make_op().compute(img)
    assert result.shape == img.shape
    assert result.dtype == np.uint8


def test_color_bgr():
    img = np.random.randint(0, 256, (64, 64, 3), dtype=np.uint8)
    result = make_op().compute(img)
    assert result.shape == img.shape
    assert result.dtype == np.uint8


def test_invalid_dtype_raises():
    img = np.random.rand(64, 64, 3).astype(np.float32)
    with pytest.raises(ValueError, match="uint8"):
        make_op().compute(img)


@pytest.mark.parametrize("name", ["tileGridSizeX", "tileGridSizeY"])
@pytest.mark.parametrize("value", [0, -1, 65])
def test_out_of_range_tile_grid_size_raises(name, value):
    img = np.random.randint(0, 256, (64, 64, 3), dtype=np.uint8)
    with pytest.raises(ValueError, match=f"'{name}' must be between 1 and 64, got {value}"):
        make_op({name: value}).compute(img)


@pytest.mark.parametrize("value", [1, 64])
def test_tile_grid_size_bounds_are_accepted(value):
    img = np.random.randint(0, 256, (64, 64, 3), dtype=np.uint8)
    result = make_op({"tileGridSizeX": value, "tileGridSizeY": value}).compute(img)
    assert result.shape == img.shape
    assert result.dtype == np.uint8

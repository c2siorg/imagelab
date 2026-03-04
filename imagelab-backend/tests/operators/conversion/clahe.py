import numpy as np
import pytest

from app.operators.conversions.clahe import claheImage


def make_op(params=None):
    op = claheImage("clahe_operator")
    op.params = params or {}
    return op


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

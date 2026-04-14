import numpy as np
import pytest

from app.operators.conversions.invert_image import InvertImage


def test_invert_uint8_bgr():
    img = np.array([[[10, 20, 30]]], dtype=np.uint8)
    result = InvertImage(params={}).compute(img)
    np.testing.assert_array_equal(result, [[[245, 235, 225]]])


def test_invert_grayscale():
    img = np.array([[0, 128, 255]], dtype=np.uint8)
    result = InvertImage(params={}).compute(img)
    np.testing.assert_array_equal(result, [[255, 127, 0]])


def test_rgba_preserves_alpha():
    img = np.array([[[10, 20, 30, 200]]], dtype=np.uint8)
    result = InvertImage(params={}).compute(img)
    assert result.shape[2] == 4
    assert result[0, 0, 3] == 200
    np.testing.assert_array_equal(result[0, 0, :3], [245, 235, 225])


def test_rejects_none():
    with pytest.raises(TypeError):
        InvertImage(params={}).compute(None)


def test_rejects_float_image():
    img = np.array([[[0.1, 0.5, 0.9]]], dtype=np.float32)
    with pytest.raises(ValueError, match="float"):
        InvertImage(params={}).compute(img)

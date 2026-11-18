import base64

import cv2
import numpy as np
import pytest

from app.operators.registry import OPERATOR_REGISTRY
from app.utils.image import decode_base64_image


def _png_b64(image: np.ndarray) -> str:
    return base64.b64encode(cv2.imencode(".png", image)[1].tobytes()).decode()


def test_16bit_gray_is_scaled_to_8bit():
    image = np.array([[0, 257, 32896, 65535]], dtype=np.uint16)
    decoded = decode_base64_image(_png_b64(image))
    assert decoded.dtype == np.uint8
    np.testing.assert_array_equal(decoded, [[0, 1, 128, 255]])


def test_16bit_color_keeps_channels():
    image = np.full((4, 6, 3), 65535, dtype=np.uint16)
    decoded = decode_base64_image(_png_b64(image))
    assert decoded.dtype == np.uint8
    assert decoded.shape == (4, 6, 3)
    assert (decoded == 255).all()


def test_16bit_rgba_keeps_alpha():
    image = np.full((4, 6, 4), 65535, dtype=np.uint16)
    decoded = decode_base64_image(_png_b64(image))
    assert decoded.shape == (4, 6, 4)
    assert decoded.dtype == np.uint8


def test_8bit_png_is_unchanged():
    image = np.arange(16, dtype=np.uint8).reshape(4, 4)
    np.testing.assert_array_equal(decode_base64_image(_png_b64(image)), image)


@pytest.mark.parametrize("operator", ["thresholding_otsuthreshold", "imageconversions_graytobinary"])
def test_threshold_of_16bit_image_gives_black_and_white(operator):
    # dark half and bright half, stored as 16-bit
    image = np.zeros((8, 8), dtype=np.uint16)
    image[:, 4:] = 60000
    decoded = decode_base64_image(_png_b64(image))
    result = OPERATOR_REGISTRY[operator]({}).compute(decoded)
    assert result.dtype == np.uint8
    assert set(np.unique(result)) == {0, 255}

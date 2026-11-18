import cv2
import numpy as np
import pytest

from app.operators.conversions.bit_plane_slicing import BitPlaneSlicing
from app.operators.registry import get_operator


def _gradient_image() -> np.ndarray:
    """1x256 grayscale image with every value from 0 to 255."""
    return np.arange(256, dtype=np.uint8).reshape(1, 256)


def test_block_is_registered():
    assert get_operator("imageconversions_bitplaneslicing") is BitPlaneSlicing


@pytest.mark.parametrize("shape", [(20, 30), (20, 30, 1), (20, 30, 3), (20, 30, 4)])
def test_output_is_single_channel_uint8(shape):
    image = np.full(shape, 100, dtype=np.uint8)
    result = BitPlaneSlicing({"bit": 5}).compute(image)
    assert result.shape == (20, 30)
    assert result.dtype == np.uint8


@pytest.mark.parametrize("bit", range(8))
def test_each_bit_matches_the_pixel_bits(bit):
    image = _gradient_image()
    expected = ((image >> bit) & 1) * 255
    np.testing.assert_array_equal(BitPlaneSlicing({"bit": bit}).compute(image), expected)


def test_known_pixel_value():
    # 150 = 0b10010110, so bits 1, 2, 4 and 7 are set
    image = np.full((1, 1), 150, dtype=np.uint8)
    results = [BitPlaneSlicing({"bit": bit}).compute(image)[0, 0] for bit in range(8)]
    assert results == [0, 255, 255, 0, 255, 0, 0, 255]


def test_default_bit_is_the_most_significant():
    result = BitPlaneSlicing({}).compute(_gradient_image())
    assert (result[0, :128] == 0).all()
    assert (result[0, 128:] == 255).all()


def test_color_image_is_converted_to_grayscale_first():
    bgr = np.random.default_rng(0).integers(0, 256, (10, 12, 3), dtype=np.uint8)
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    np.testing.assert_array_equal(BitPlaneSlicing({"bit": 6}).compute(bgr), BitPlaneSlicing({"bit": 6}).compute(gray))


def test_alpha_channel_is_ignored():
    bgr = np.full((4, 4, 3), 200, dtype=np.uint8)
    transparent = np.dstack([bgr, np.zeros((4, 4), dtype=np.uint8)])
    opaque = np.dstack([bgr, np.full((4, 4), 255, dtype=np.uint8)])
    expected = BitPlaneSlicing({"bit": 7}).compute(bgr)
    np.testing.assert_array_equal(BitPlaneSlicing({"bit": 7}).compute(transparent), expected)
    np.testing.assert_array_equal(BitPlaneSlicing({"bit": 7}).compute(opaque), expected)


@pytest.mark.parametrize("bit", [-1, 8, 100])
def test_invalid_bit_is_rejected(bit):
    with pytest.raises(ValueError, match="'bit' must be between 0 and 7"):
        BitPlaneSlicing({"bit": bit}).compute(_gradient_image())


def test_float_image_is_rejected():
    with pytest.raises(ValueError, match="uint8"):
        BitPlaneSlicing({"bit": 7}).compute(np.zeros((4, 4), dtype=np.float32))

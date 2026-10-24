import numpy as np
import pytest

from app.operators.conversions.gamma_correction import GammaCorrection
from app.operators.registry import get_operator


def _gradient_image() -> np.ndarray:
    """1x256 grayscale image with every value from 0 to 255."""
    return np.arange(256, dtype=np.uint8).reshape(1, 256)


def test_block_is_registered():
    assert get_operator("imageconversions_gammacorrection") is GammaCorrection


@pytest.mark.parametrize("shape", [(20, 30), (20, 30, 3), (20, 30, 4)])
def test_output_keeps_shape_and_dtype(shape):
    image = np.full(shape, 100, dtype=np.uint8)
    result = GammaCorrection({"gamma": 2.0}).compute(image)
    assert result.shape == image.shape
    assert result.dtype == np.uint8


def test_gamma_one_leaves_image_unchanged():
    image = _gradient_image()
    np.testing.assert_array_equal(GammaCorrection({"gamma": 1.0}).compute(image), image)


def test_gamma_above_one_brightens_midtones():
    result = GammaCorrection({"gamma": 2.0}).compute(_gradient_image())
    assert result[0, 64] == 128
    assert result[0, 128] > 128


def test_gamma_below_one_darkens_midtones():
    result = GammaCorrection({"gamma": 0.5}).compute(_gradient_image())
    assert result[0, 128] < 128


@pytest.mark.parametrize("gamma", [0.5, 2.0])
def test_black_and_white_stay_fixed(gamma):
    result = GammaCorrection({"gamma": gamma}).compute(_gradient_image())
    assert result[0, 0] == 0
    assert result[0, 255] == 255


def test_alpha_channel_is_preserved():
    image = np.zeros((4, 4, 4), dtype=np.uint8)
    image[:, :, :3] = 128
    image[:, :, 3] = 77
    result = GammaCorrection({"gamma": 2.0}).compute(image)
    assert (result[:, :, 3] == 77).all()
    assert (result[:, :, :3] > 128).all()


@pytest.mark.parametrize("gamma", [0, -1, 0.05, 5.5])
def test_invalid_gamma_is_rejected(gamma):
    with pytest.raises(ValueError, match="'gamma' must be between"):
        GammaCorrection({"gamma": gamma}).compute(_gradient_image())

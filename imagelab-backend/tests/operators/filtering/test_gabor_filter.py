import numpy as np
import pytest

from app.operators.filtering.gabor_filter import GaborFilter
from app.operators.registry import get_operator


def _vertical_stripes() -> np.ndarray:
    """64x64 grayscale image with a white vertical line every 10 pixels."""
    img = np.zeros((64, 64), dtype=np.uint8)
    img[:, ::10] = 255
    return img


def test_block_is_registered():
    assert get_operator("filtering_gaborfilter") is GaborFilter


@pytest.mark.parametrize("shape", [(40, 50), (40, 50, 3), (40, 50, 4)])
def test_output_is_3_channel_uint8_with_same_size(shape):
    image = np.random.default_rng(0).integers(0, 256, shape, dtype=np.uint8)
    result = GaborFilter({}).compute(image)
    assert result.shape == (40, 50, 3)
    assert result.dtype == np.uint8


def test_grayscale_result_has_equal_channels():
    result = GaborFilter({}).compute(_vertical_stripes())
    assert (result[:, :, 0] == result[:, :, 1]).all()
    assert (result[:, :, 1] == result[:, :, 2]).all()


def test_output_is_stretched_to_full_range():
    result = GaborFilter({}).compute(_vertical_stripes())
    assert result.min() == 0
    assert result.max() == 255


def test_large_image_keeps_original_size():
    image = np.zeros((1000, 1600, 3), dtype=np.uint8)
    result = GaborFilter({}).compute(image)
    assert result.shape == (1000, 1600, 3)


def test_theta_matches_stripe_direction():
    image = _vertical_stripes()
    along = GaborFilter({"theta": 0}).compute(image)
    across = GaborFilter({"theta": 90}).compute(image)
    assert along.mean() > across.mean()


@pytest.mark.parametrize("kernel_size", [0, 4, 100])
def test_out_of_range_kernel_size_does_not_crash(kernel_size):
    result = GaborFilter({"kernelSize": kernel_size}).compute(_vertical_stripes())
    assert result.shape == (64, 64, 3)


def test_too_small_sigma_lambda_gamma_are_clamped():
    params = {"sigma": -5, "lambda_": 0, "gamma": 0}
    result = GaborFilter(params).compute(_vertical_stripes())
    assert result.shape == (64, 64, 3)


def test_rejects_empty_image():
    with pytest.raises(ValueError, match="invalid dimensions"):
        GaborFilter({}).compute(np.zeros((0, 5), dtype=np.uint8))

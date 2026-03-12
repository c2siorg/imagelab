import numpy as np
import pytest

from app.operators.blurring.median_blur import MedianBlur


@pytest.fixture
def image():
    """A small solid-colour image reused across all MedianBlur tests."""
    return np.full((5, 5, 3), 128, dtype=np.uint8)


class TestMedianBlurValidInput:
    def test_default_params_produce_output(self, image):
        result = MedianBlur({}).compute(image)
        assert result.shape == image.shape
        assert result.dtype == image.dtype

    @pytest.mark.parametrize("size", [1, 3, 5, 7, 9])
    def test_valid_odd_kernel_sizes(self, image, size):
        result = MedianBlur({"kernelSize": size}).compute(image)
        assert result.shape == image.shape


class TestMedianBlurInvalidInput:
    @pytest.mark.parametrize("even_size", [2, 4, 6, 100])
    def test_even_kernel_size_auto_corrected(self, image, even_size):
        result = MedianBlur({"kernelSize": even_size}).compute(image)
        assert result.shape == image.shape

    @pytest.mark.parametrize("bad_size", [0, -1, -5])
    def test_kernel_size_below_minimum_raises(self, image, bad_size):
        """Values < 1 are invalid; the error message must reference the minimum."""
        with pytest.raises(ValueError, match=">= 1"):
            MedianBlur({"kernelSize": bad_size}).compute(image)



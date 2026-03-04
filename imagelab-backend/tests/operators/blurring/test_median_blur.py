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

    @pytest.mark.parametrize("size", [3, 5, 7, 9])
    def test_valid_odd_kernel_sizes(self, image, size):
        result = MedianBlur({"kernelSize": size}).compute(image)
        assert result.shape == image.shape


class TestMedianBlurInvalidInput:
    @pytest.mark.parametrize("bad_size", [2, 4, 6, 100])
    def test_even_kernel_size_raises(self, image, bad_size):
        with pytest.raises(ValueError, match="'kernelSize'"):
            MedianBlur({"kernelSize": bad_size}).compute(image)

    @pytest.mark.parametrize("bad_size", [1, 0, -1, -5])
    def test_kernel_size_below_minimum_raises(self, image, bad_size):
        """Values < 3 are invalid; the error message must reference the minimum."""
        with pytest.raises(ValueError, match=">= 3"):
            MedianBlur({"kernelSize": bad_size}).compute(image)

    def test_even_error_suggests_neighbours(self, image):
        with pytest.raises(ValueError, match="3|5"):
            MedianBlur({"kernelSize": 4}).compute(image)

    def test_error_message_is_user_friendly(self, image):
        with pytest.raises(ValueError, match="odd"):
            MedianBlur({"kernelSize": 2}).compute(image)

    def test_no_silent_autofix_for_even_input(self, image):
        # Previously, even values were silently incremented to odd. Now a
        # ValueError must be raised instead of silently accepting the input.
        with pytest.raises(ValueError):
            MedianBlur({"kernelSize": 4}).compute(image)

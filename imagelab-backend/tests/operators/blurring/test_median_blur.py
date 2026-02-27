import numpy as np
import pytest

from app.operators.blurring.median_blur import MedianBlur

IMAGE = np.full((5, 5, 3), 128, dtype=np.uint8)


class TestMedianBlurValidInput:
    def test_default_params_produce_output(self):
        result = MedianBlur({}).compute(IMAGE)
        assert result.shape == IMAGE.shape
        assert result.dtype == IMAGE.dtype

    @pytest.mark.parametrize("size", [3, 5, 7, 9])
    def test_valid_odd_kernel_sizes(self, size):
        result = MedianBlur({"kernelSize": size}).compute(IMAGE)
        assert result.shape == IMAGE.shape


class TestMedianBlurInvalidInput:
    @pytest.mark.parametrize("bad_size", [2, 4, 6, 100])
    def test_even_kernel_size_raises(self, bad_size):
        with pytest.raises(ValueError, match="'kernelSize'"):
            MedianBlur({"kernelSize": bad_size}).compute(IMAGE)

    @pytest.mark.parametrize("bad_size", [1, 0, -1, -5])
    def test_kernel_size_not_greater_than_one_raises(self, bad_size):
        with pytest.raises(ValueError, match="greater than 1"):
            MedianBlur({"kernelSize": bad_size}).compute(IMAGE)

    def test_even_error_suggests_neighbours(self):
        with pytest.raises(ValueError, match="3|5"):
            MedianBlur({"kernelSize": 4}).compute(IMAGE)

    def test_error_message_is_user_friendly(self):
        with pytest.raises(ValueError, match="odd"):
            MedianBlur({"kernelSize": 2}).compute(IMAGE)

    def test_no_silent_autofix_for_even_input(self):
        # Previously, even values were silently incremented to odd. Now a
        # ValueError must be raised instead of silently accepting the input.
        with pytest.raises(ValueError):
            MedianBlur({"kernelSize": 4}).compute(IMAGE)

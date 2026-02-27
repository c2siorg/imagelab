import numpy as np
import pytest

from app.operators.blurring.gaussian_blur import GaussianBlur

IMAGE = np.full((5, 5, 3), 128, dtype=np.uint8)


class TestGaussianBlurValidInput:
    def test_default_params_produce_output(self):
        result = GaussianBlur({}).compute(IMAGE)
        assert result.shape == IMAGE.shape
        assert result.dtype == IMAGE.dtype

    @pytest.mark.parametrize("size", [1, 3, 5, 7])
    def test_odd_kernel_sizes_are_accepted(self, size):
        result = GaussianBlur({"widthSize": size, "heightSize": size}).compute(IMAGE)
        assert result.shape == IMAGE.shape

    def test_different_width_and_height(self):
        result = GaussianBlur({"widthSize": 3, "heightSize": 5}).compute(IMAGE)
        assert result.shape == IMAGE.shape


class TestGaussianBlurInvalidInput:
    @pytest.mark.parametrize("bad_size", [2, 4, 6, 100])
    def test_even_width_raises(self, bad_size):
        with pytest.raises(ValueError, match="'widthSize'"):
            GaussianBlur({"widthSize": bad_size, "heightSize": 3}).compute(IMAGE)

    @pytest.mark.parametrize("bad_size", [2, 4, 6, 100])
    def test_even_height_raises(self, bad_size):
        with pytest.raises(ValueError, match="'heightSize'"):
            GaussianBlur({"widthSize": 3, "heightSize": bad_size}).compute(IMAGE)

    @pytest.mark.parametrize("bad_size", [0, -1, -5])
    def test_non_positive_width_raises(self, bad_size):
        with pytest.raises(ValueError, match="'widthSize'"):
            GaussianBlur({"widthSize": bad_size, "heightSize": 3}).compute(IMAGE)

    @pytest.mark.parametrize("bad_size", [0, -1, -5])
    def test_non_positive_height_raises(self, bad_size):
        with pytest.raises(ValueError, match="'heightSize'"):
            GaussianBlur({"widthSize": 3, "heightSize": bad_size}).compute(IMAGE)

    def test_even_error_suggests_neighbours(self):
        with pytest.raises(ValueError, match="3|5"):
            GaussianBlur({"widthSize": 4, "heightSize": 3}).compute(IMAGE)

    def test_error_message_is_user_friendly(self):
        with pytest.raises(ValueError, match="odd"):
            GaussianBlur({"widthSize": 2}).compute(IMAGE)

    def test_no_silent_autofix_for_even_input(self):
        # Previously, even values were silently incremented to odd. Now a
        # ValueError must be raised instead of silently accepting the input.
        with pytest.raises(ValueError):
            GaussianBlur({"widthSize": 4, "heightSize": 4}).compute(IMAGE)

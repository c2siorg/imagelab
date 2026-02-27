import numpy as np
import pytest

from app.operators.blurring.blur import Blur

# A tiny valid image used across all tests
IMAGE = np.full((5, 5, 3), 128, dtype=np.uint8)


class TestBlurValidInput:
    def test_default_params_produce_output(self):
        result = Blur({}).compute(IMAGE)
        assert result.shape == IMAGE.shape
        assert result.dtype == IMAGE.dtype

    def test_explicit_valid_dimensions(self):
        result = Blur({"widthSize": 3, "heightSize": 3}).compute(IMAGE)
        assert result.shape == IMAGE.shape

    def test_even_kernel_sizes_are_accepted(self):
        # Plain blur supports any positive integer, including even values
        result = Blur({"widthSize": 2, "heightSize": 4}).compute(IMAGE)
        assert result.shape == IMAGE.shape

    def test_width_one_is_valid(self):
        result = Blur({"widthSize": 1, "heightSize": 1}).compute(IMAGE)
        assert result.shape == IMAGE.shape


class TestBlurInvalidInput:
    @pytest.mark.parametrize("bad_width", [0, -1, -10])
    def test_non_positive_width_raises(self, bad_width):
        with pytest.raises(ValueError, match="'widthSize'"):
            Blur({"widthSize": bad_width, "heightSize": 3}).compute(IMAGE)

    @pytest.mark.parametrize("bad_height", [0, -1, -10])
    def test_non_positive_height_raises(self, bad_height):
        with pytest.raises(ValueError, match="'heightSize'"):
            Blur({"widthSize": 3, "heightSize": bad_height}).compute(IMAGE)

    def test_error_message_is_user_friendly(self):
        with pytest.raises(ValueError, match="positive integer"):
            Blur({"widthSize": 0}).compute(IMAGE)

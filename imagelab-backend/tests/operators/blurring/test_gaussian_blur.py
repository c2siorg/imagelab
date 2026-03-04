import numpy as np
import pytest

from app.operators.blurring.gaussian_blur import GaussianBlur


@pytest.fixture
def image():
    """A small solid-colour image reused across all GaussianBlur tests."""
    return np.full((5, 5, 3), 128, dtype=np.uint8)


class TestGaussianBlurValidInput:
    def test_default_params_produce_output(self, image):
        result = GaussianBlur({}).compute(image)
        assert result.shape == image.shape
        assert result.dtype == image.dtype

    @pytest.mark.parametrize("size", [1, 3, 5, 7])
    def test_odd_kernel_sizes_are_accepted(self, image, size):
        result = GaussianBlur({"widthSize": size, "heightSize": size}).compute(image)
        assert result.shape == image.shape

    def test_different_width_and_height(self, image):
        result = GaussianBlur({"widthSize": 3, "heightSize": 5}).compute(image)
        assert result.shape == image.shape


class TestGaussianBlurInvalidInput:
    @pytest.mark.parametrize("bad_size", [2, 4, 6, 100])
    def test_even_width_raises(self, image, bad_size):
        with pytest.raises(ValueError, match="'widthSize'"):
            GaussianBlur({"widthSize": bad_size, "heightSize": 3}).compute(image)

    @pytest.mark.parametrize("bad_size", [2, 4, 6, 100])
    def test_even_height_raises(self, image, bad_size):
        with pytest.raises(ValueError, match="'heightSize'"):
            GaussianBlur({"widthSize": 3, "heightSize": bad_size}).compute(image)

    @pytest.mark.parametrize("bad_size", [0, -1, -5])
    def test_non_positive_width_raises(self, image, bad_size):
        with pytest.raises(ValueError, match="'widthSize'"):
            GaussianBlur({"widthSize": bad_size, "heightSize": 3}).compute(image)

    @pytest.mark.parametrize("bad_size", [0, -1, -5])
    def test_non_positive_height_raises(self, image, bad_size):
        with pytest.raises(ValueError, match="'heightSize'"):
            GaussianBlur({"widthSize": 3, "heightSize": bad_size}).compute(image)

    @pytest.mark.parametrize(
        "even, expected_lower, expected_upper",
        [
            (2, 1, 3),
            (4, 3, 5),
            (100, 99, 101),
        ],
    )
    def test_even_error_suggests_neighbours(self, image, even, expected_lower, expected_upper):
        """Both neighbours are valid for GaussianBlur (min_value=1)."""
        with pytest.raises(ValueError, match=f"{expected_lower}|{expected_upper}"):
            GaussianBlur({"widthSize": even, "heightSize": 3}).compute(image)

    def test_error_message_is_user_friendly(self, image):
        with pytest.raises(ValueError, match="odd"):
            GaussianBlur({"widthSize": 2}).compute(image)

    def test_no_silent_autofix_for_even_input(self, image):
        # Previously, even values were silently incremented to odd. Now a
        # ValueError must be raised instead of silently accepting the input.
        with pytest.raises(ValueError):
            GaussianBlur({"widthSize": 4, "heightSize": 4}).compute(image)

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
    @pytest.mark.parametrize("even_size", [2, 4, 6, 100])
    def test_even_sizes_auto_corrected(self, image, even_size):
        # Should not raise; should produce valid output
        result = GaussianBlur({"widthSize": even_size, "heightSize": even_size}).compute(image)
        assert result.shape == image.shape

    @pytest.mark.parametrize("bad_size", [0, -1, -5])
    def test_non_positive_width_raises(self, image, bad_size):
        with pytest.raises(ValueError, match="'widthSize'"):
            GaussianBlur({"widthSize": bad_size, "heightSize": 3}).compute(image)

    @pytest.mark.parametrize("bad_size", [0, -1, -5])
    def test_non_positive_height_raises(self, image, bad_size):
        with pytest.raises(ValueError, match="'heightSize'"):
            GaussianBlur({"widthSize": 3, "heightSize": bad_size}).compute(image)



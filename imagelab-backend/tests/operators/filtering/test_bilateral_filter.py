import numpy as np
import pytest

from app.operators.filtering.bilateral_filter import BilateralFilter


@pytest.fixture
def image():
    return np.full((5, 5, 3), 128, dtype=np.uint8)


class TestBilateralFilterValidInput:
    def test_default_params_produce_output(self, image):
        result = BilateralFilter({}).compute(image)
        assert result.shape == image.shape
        assert result.dtype == image.dtype

    @pytest.mark.parametrize("size", [1, 3, 5, 9])
    def test_positive_filter_sizes(self, image, size):
        result = BilateralFilter({"filterSize": size}).compute(image)
        assert result.shape == image.shape


class TestBilateralFilterInvalidInput:
    @pytest.mark.parametrize("bad_size", [0, -1, -5])
    def test_non_positive_filter_size_raises(self, image, bad_size):
        with pytest.raises(ValueError, match="'filterSize'"):
            BilateralFilter({"filterSize": bad_size}).compute(image)

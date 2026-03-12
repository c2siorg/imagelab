import numpy as np
import pytest

from app.operators.segmentation.mean_shift_segmentation import MeanShiftSegmentation


@pytest.fixture
def color_image():
    return np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)


@pytest.fixture
def grayscale_image():
    return np.random.randint(0, 256, (100, 100), dtype=np.uint8)


@pytest.fixture
def rgba_image():
    return np.random.randint(0, 256, (100, 100, 4), dtype=np.uint8)


class TestMeanShiftSegmentation:
    def test_default_params_output_shape(self, color_image):
        result = MeanShiftSegmentation({}).compute(color_image)
        assert result.shape == color_image.shape

    def test_output_is_uint8(self, color_image):
        result = MeanShiftSegmentation({}).compute(color_image)
        assert result.dtype == np.uint8

    def test_custom_params_output_shape(self, color_image):
        result = MeanShiftSegmentation({"sp": 10, "sr": 30, "maxLevel": 2}).compute(color_image)
        assert result.shape == color_image.shape

    def test_grayscale_input_returns_bgr(self, grayscale_image):
        result = MeanShiftSegmentation({}).compute(grayscale_image)
        assert result.shape == (100, 100, 3)
        assert result.dtype == np.uint8

    def test_rgba_input_converted_to_bgr(self, rgba_image):
        result = MeanShiftSegmentation({}).compute(rgba_image)
        assert result.shape == (100, 100, 3)
        assert result.dtype == np.uint8

    def test_output_values_in_range(self, color_image):
        result = MeanShiftSegmentation({}).compute(color_image)
        assert result.min() >= 0
        assert result.max() <= 255

    def test_max_level_zero(self, color_image):
        result = MeanShiftSegmentation({"maxLevel": 0}).compute(color_image)
        assert result.shape == color_image.shape

    def test_high_colour_radius_simplifies_image(self, color_image):
        result = MeanShiftSegmentation({"sr": 200}).compute(color_image)
        assert result.shape == color_image.shape
        assert result.dtype == np.uint8

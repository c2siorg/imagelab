import cv2
import numpy as np
import pytest

from app.operators.filtering.bilateral_filter import BilateralFilter
from app.operators.filtering.box_filter import BoxFilter
from app.operators.filtering.dilation import Dilation
from app.operators.filtering.erosion import Erosion
from app.operators.filtering.morphological import Morphological
from app.operators.filtering.pyramid_down import PyramidDown
from app.operators.filtering.pyramid_up import PyramidUp
from app.operators.filtering.sharpen import Sharpen


@pytest.fixture
def color_image():
    return np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)


@pytest.fixture
def grayscale_image():
    return np.random.randint(0, 256, (100, 100), dtype=np.uint8)


@pytest.fixture
def rgba_image():
    return np.random.randint(0, 256, (100, 100, 4), dtype=np.uint8)


# BilateralFilter


class TestBilateralFilter:
    def test_default_params_output_shape(self, color_image):
        result = BilateralFilter({}).compute(color_image)
        assert result.shape == color_image.shape

    def test_custom_params_output_shape(self, color_image):
        result = BilateralFilter({"filterSize": 9, "sigmaColor": 50, "sigmaSpace": 50}).compute(color_image)
        assert result.shape == color_image.shape

    def test_grayscale_input(self, grayscale_image):
        result = BilateralFilter({}).compute(grayscale_image)
        assert result.shape == grayscale_image.shape

    def test_rgba_input_converted_to_bgr(self, rgba_image):
        result = BilateralFilter({}).compute(rgba_image)
        assert result.shape[2] == 3

    def test_output_is_uint8(self, color_image):
        result = BilateralFilter({}).compute(color_image)
        assert result.dtype == np.uint8


# BoxFilter


class TestBoxFilter:
    def test_default_params_output_shape(self, color_image):
        result = BoxFilter({"depth": -1}).compute(color_image)
        assert result.shape == color_image.shape

    def test_custom_params_output_shape(self, color_image):
        result = BoxFilter({"width": 10, "height": 10, "depth": -1}).compute(color_image)
        assert result.shape == color_image.shape

    def test_grayscale_input(self, grayscale_image):
        result = BoxFilter({"width": 5, "height": 5, "depth": -1}).compute(grayscale_image)
        assert result.shape == grayscale_image.shape

    def test_custom_anchor_point(self, color_image):
        result = BoxFilter({"width": 5, "height": 5, "depth": -1, "point_x": 0, "point_y": 0}).compute(color_image)
        assert result.shape == color_image.shape

    def test_output_is_uint8(self, color_image):
        result = BoxFilter({"depth": -1}).compute(color_image)
        assert result.dtype == np.uint8

    def test_asymmetric_kernel_uses_width_height_convention(self):
        image = np.arange(75, dtype=np.uint8).reshape(5, 5, 3)
        width, height = 1, 5

        result = BoxFilter({"width": width, "height": height, "depth": -1}).compute(
            image
        )
        expected = cv2.boxFilter(
            image,
            -1,
            (width, height),
            anchor=(-1, -1),
            normalize=True,
            borderType=cv2.BORDER_DEFAULT,
        )

        np.testing.assert_array_equal(result, expected)


# Sharpen


class TestSharpen:
    def test_default_params_output_shape(self, color_image):
        result = Sharpen({}).compute(color_image)
        assert result.shape == color_image.shape

    def test_grayscale_input(self, grayscale_image):
        result = Sharpen({}).compute(grayscale_image)
        assert result.shape == grayscale_image.shape

    def test_zero_strength_returns_original(self, color_image):
        result = Sharpen({"strength": 0.0}).compute(color_image)
        np.testing.assert_array_equal(result, color_image)

    def test_strength_clamped_above_max(self, color_image):
        result = Sharpen({"strength": 5.0}).compute(color_image)
        assert result.shape == color_image.shape

    def test_strength_clamped_below_zero(self, color_image):
        result = Sharpen({"strength": -1.0}).compute(color_image)
        np.testing.assert_array_equal(result, color_image)

    def test_rgba_input_converted_to_bgr(self, rgba_image):
        result = Sharpen({}).compute(rgba_image)
        assert result.shape[2] == 3

    def test_output_is_uint8(self, color_image):
        result = Sharpen({}).compute(color_image)
        assert result.dtype == np.uint8


# Erosion


class TestErosion:
    def test_default_params_output_shape(self, color_image):
        result = Erosion({}).compute(color_image)
        assert result.shape == color_image.shape

    def test_grayscale_input(self, grayscale_image):
        result = Erosion({}).compute(grayscale_image)
        assert result.shape == grayscale_image.shape

    def test_multiple_iterations(self, color_image):
        result = Erosion({"iteration": 3}).compute(color_image)
        assert result.shape == color_image.shape

    def test_output_is_uint8(self, color_image):
        result = Erosion({}).compute(color_image)
        assert result.dtype == np.uint8

    def test_erodes_bright_regions(self):
        image = np.zeros((50, 50, 3), dtype=np.uint8)
        image[20:30, 20:30] = 255
        result = Erosion({}).compute(image)
        assert result.sum() <= image.sum()


# Dilation


class TestDilation:
    def test_default_params_output_shape(self, color_image):
        result = Dilation({}).compute(color_image)
        assert result.shape == color_image.shape

    def test_grayscale_input(self, grayscale_image):
        result = Dilation({}).compute(grayscale_image)
        assert result.shape == grayscale_image.shape

    def test_multiple_iterations(self, color_image):
        result = Dilation({"iteration": 3}).compute(color_image)
        assert result.shape == color_image.shape

    def test_output_is_uint8(self, color_image):
        result = Dilation({}).compute(color_image)
        assert result.dtype == np.uint8

    def test_dilates_bright_regions(self):
        image = np.zeros((50, 50, 3), dtype=np.uint8)
        image[20:30, 20:30] = 255
        result = Dilation({}).compute(image)
        assert result.sum() >= image.sum()


# Morphological


class TestMorphological:
    @pytest.mark.parametrize("morph_type", ["OPEN", "CLOSE", "GRADIENT", "TOPHAT", "BLACKHAT"])
    def test_all_types_output_shape(self, color_image, morph_type):
        result = Morphological({"type": morph_type}).compute(color_image)
        assert result.shape[:2] == color_image.shape[:2]

    def test_default_type_output_shape(self, color_image):
        result = Morphological({}).compute(color_image)
        assert result.shape[:2] == color_image.shape[:2]

    def test_grayscale_input(self, grayscale_image):
        result = Morphological({"type": "OPEN"}).compute(grayscale_image)
        assert result.shape == grayscale_image.shape

    def test_rgba_input_converted_for_gradient(self, rgba_image):
        result = Morphological({"type": "GRADIENT"}).compute(rgba_image)
        assert result.shape[2] == 3

    def test_output_is_uint8(self, color_image):
        result = Morphological({"type": "OPEN"}).compute(color_image)
        assert result.dtype == np.uint8


# PyramidUp


class TestPyramidUp:
    def test_output_shape_doubled(self, color_image):
        result = PyramidUp({}).compute(color_image)
        assert result.shape[0] == color_image.shape[0] * 2
        assert result.shape[1] == color_image.shape[1] * 2

    def test_grayscale_input(self, grayscale_image):
        result = PyramidUp({}).compute(grayscale_image)
        assert result.shape[0] == grayscale_image.shape[0] * 2
        assert result.shape[1] == grayscale_image.shape[1] * 2

    def test_output_is_uint8(self, color_image):
        result = PyramidUp({}).compute(color_image)
        assert result.dtype == np.uint8


# PyramidDown


class TestPyramidDown:
    def test_output_shape_halved(self, color_image):
        result = PyramidDown({}).compute(color_image)
        assert result.shape[0] == color_image.shape[0] // 2
        assert result.shape[1] == color_image.shape[1] // 2

    def test_grayscale_input(self, grayscale_image):
        result = PyramidDown({}).compute(grayscale_image)
        assert result.shape[0] == grayscale_image.shape[0] // 2
        assert result.shape[1] == grayscale_image.shape[1] // 2

    def test_output_is_uint8(self, color_image):
        result = PyramidDown({}).compute(color_image)
        assert result.dtype == np.uint8

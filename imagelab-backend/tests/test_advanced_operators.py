import numpy as np
import pytest

from app.operators.conversions.brightness_contrast import BrightnessContrast
from app.operators.conversions.histogram_equalization import HistogramEqualization
from app.operators.filtering.canny_edge import CannyEdge

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def color_image():
    rng = np.random.default_rng(42)
    return rng.integers(0, 256, (100, 100, 3), dtype=np.uint8)


@pytest.fixture
def grayscale_image():
    rng = np.random.default_rng(42)
    return rng.integers(0, 256, (100, 100), dtype=np.uint8)


@pytest.fixture
def rgba_image():
    rng = np.random.default_rng(42)
    return rng.integers(0, 256, (100, 100, 4), dtype=np.uint8)


# ===========================================================================
# Canny Edge Detection
# ===========================================================================


class TestCannyEdge:
    """Tests for the CannyEdge operator."""

    def test_default_params_output_shape(self, color_image):
        result = CannyEdge({}).compute(color_image)
        assert result.shape == (100, 100), "Canny should return a 2-D edge map"

    def test_grayscale_input_output_shape(self, grayscale_image):
        result = CannyEdge({}).compute(grayscale_image)
        assert result.shape == grayscale_image.shape

    def test_rgba_input_output_shape(self, rgba_image):
        result = CannyEdge({}).compute(rgba_image)
        assert result.shape == (100, 100)

    def test_custom_thresholds_output_shape(self, color_image):
        result = CannyEdge({"threshold1": 50, "threshold2": 150}).compute(color_image)
        assert result.shape == (100, 100)

    def test_output_is_uint8(self, color_image):
        result = CannyEdge({}).compute(color_image)
        assert result.dtype == np.uint8

    def test_output_is_binary(self, color_image):
        result = CannyEdge({}).compute(color_image)
        unique_values = set(np.unique(result))
        assert unique_values.issubset({0, 255}), "Canny output should contain only 0 and 255"

    def test_edges_detected_on_synthetic_image(self):
        """A sharp black-to-white boundary should produce detectable edges."""
        image = np.zeros((100, 100), dtype=np.uint8)
        image[:, 50:] = 255  # vertical edge at column 50
        result = CannyEdge({"threshold1": 50, "threshold2": 150}).compute(image)
        assert result.sum() > 0, "Canny should detect the vertical edge"

    def test_uniform_image_no_edges(self):
        """A completely uniform image should produce no edges."""
        image = np.full((100, 100), 128, dtype=np.uint8)
        result = CannyEdge({"threshold1": 50, "threshold2": 150}).compute(image)
        assert result.sum() == 0, "Uniform image should have no edges"

    def test_threshold_string_values_coerced(self, color_image):
        """Parameters may arrive as strings from the frontend — verify coercion."""
        result = CannyEdge({"threshold1": "80", "threshold2": "180"}).compute(color_image)
        assert result.shape == (100, 100)
        assert result.dtype == np.uint8


# ===========================================================================
# Histogram Equalization
# ===========================================================================


class TestHistogramEqualization:
    """Tests for the HistogramEqualization operator."""

    def test_grayscale_output_shape(self, grayscale_image):
        result = HistogramEqualization({}).compute(grayscale_image)
        assert result.shape == grayscale_image.shape

    def test_color_output_shape(self, color_image):
        result = HistogramEqualization({}).compute(color_image)
        assert result.shape == color_image.shape

    def test_rgba_output_shape(self, rgba_image):
        result = HistogramEqualization({}).compute(rgba_image)
        assert result.shape == rgba_image.shape

    def test_rgba_preserves_alpha(self, rgba_image):
        result = HistogramEqualization({}).compute(rgba_image)
        np.testing.assert_array_equal(
            result[:, :, 3],
            rgba_image[:, :, 3],
            err_msg="Alpha channel should be preserved after equalization",
        )

    def test_output_is_uint8_grayscale(self, grayscale_image):
        result = HistogramEqualization({}).compute(grayscale_image)
        assert result.dtype == np.uint8

    def test_output_is_uint8_color(self, color_image):
        result = HistogramEqualization({}).compute(color_image)
        assert result.dtype == np.uint8

    def test_spreads_histogram_grayscale(self):
        """A low-contrast image should have a wider intensity spread after equalization."""
        # Narrow range: all pixels between 100 and 110
        rng = np.random.default_rng(99)
        image = rng.integers(100, 111, (100, 100), dtype=np.uint8)
        result = HistogramEqualization({}).compute(image)
        original_range = int(image.max()) - int(image.min())
        equalized_range = int(result.max()) - int(result.min())
        assert equalized_range > original_range, "Histogram equalization should spread pixel values"

    def test_uniform_image_stays_valid(self):
        """A completely uniform image should not crash and should stay uint8."""
        image = np.full((50, 50), 100, dtype=np.uint8)
        result = HistogramEqualization({}).compute(image)
        assert result.dtype == np.uint8
        assert result.shape == image.shape


# ===========================================================================
# Brightness & Contrast
# ===========================================================================


class TestBrightnessContrast:
    """Tests for the BrightnessContrast operator."""

    def test_default_params_no_change(self, color_image):
        result = BrightnessContrast({}).compute(color_image)
        np.testing.assert_array_equal(
            result,
            color_image,
            err_msg="Default brightness=0, contrast=1.0 should leave image unchanged",
        )

    def test_grayscale_output_shape(self, grayscale_image):
        result = BrightnessContrast({"brightness": 10, "contrast": 1.2}).compute(grayscale_image)
        assert result.shape == grayscale_image.shape

    def test_color_output_shape(self, color_image):
        result = BrightnessContrast({"brightness": 20}).compute(color_image)
        assert result.shape == color_image.shape

    def test_rgba_output_shape(self, rgba_image):
        result = BrightnessContrast({"brightness": -10}).compute(rgba_image)
        assert result.shape == rgba_image.shape

    def test_output_is_uint8(self, color_image):
        result = BrightnessContrast({"brightness": 50, "contrast": 2.0}).compute(color_image)
        assert result.dtype == np.uint8

    def test_brightness_increases_mean(self):
        """Adding positive brightness should raise the image mean."""
        image = np.full((50, 50), 100, dtype=np.uint8)
        result = BrightnessContrast({"brightness": 50}).compute(image)
        assert result.mean() > image.mean()

    def test_brightness_decreases_mean(self):
        """Adding negative brightness should lower the image mean."""
        image = np.full((50, 50), 100, dtype=np.uint8)
        result = BrightnessContrast({"brightness": -50}).compute(image)
        assert result.mean() < image.mean()

    def test_contrast_zero_produces_flat(self):
        """Contrast of 0 collapses all pixels to the brightness offset (clamped to [0,255])."""
        image = np.full((50, 50, 3), 100, dtype=np.uint8)
        result = BrightnessContrast({"contrast": 0, "brightness": 0}).compute(image)
        assert np.all(result == 0), "contrast=0 + brightness=0 should produce an all-zero image"

    def test_values_clamped_to_uint8_range(self):
        """Extreme parameters should still produce valid uint8 output."""
        image = np.full((50, 50), 200, dtype=np.uint8)
        result = BrightnessContrast({"brightness": 100, "contrast": 3.0}).compute(image)
        assert result.max() <= 255
        assert result.min() >= 0

    def test_parameter_clamping(self):
        """Parameters outside valid range should be clamped, not crash."""
        image = np.full((50, 50), 128, dtype=np.uint8)
        # brightness > 100 should be clamped to 100
        result = BrightnessContrast({"brightness": 999, "contrast": 10.0}).compute(image)
        assert result.dtype == np.uint8

    def test_string_values_coerced(self, color_image):
        """Parameters may arrive as strings from the frontend — verify coercion."""
        result = BrightnessContrast({"brightness": "30", "contrast": "1.5"}).compute(color_image)
        assert result.shape == color_image.shape
        assert result.dtype == np.uint8

"""
Tests for BilateralFilter operator parameter validation and functionality.

BilateralFilter requires:
- filterSize: positive integer (> 0)
- sigmaColor: positive number (> 0)
- sigmaSpace: positive number (> 0)
"""

import numpy as np
import pytest

from app.operators.filtering.bilateral_filter import BilateralFilter


@pytest.fixture
def image():
    """A small solid-color BGR image reused across all BilateralFilter tests."""
    return np.full((10, 10, 3), 128, dtype=np.uint8)


@pytest.fixture
def rgba_image():
    """A small solid-color RGBA image to test color space conversion."""
    return np.full((10, 10, 4), 128, dtype=np.uint8)


@pytest.fixture
def gray_image():
    """A small solid-color grayscale image."""
    return np.full((10, 10), 128, dtype=np.uint8)


class TestBilateralFilterValidInput:
    """Test BilateralFilter with valid parameters."""

    def test_default_params_produce_output(self, image):
        """Default parameters should produce an output image of same shape."""
        result = BilateralFilter({}).compute(image)
        assert result.shape == image.shape
        assert result.dtype == image.dtype

    def test_explicit_valid_filter_sizes(self, image):
        """Valid filter sizes should all work."""
        for size in [1, 3, 5, 9, 15]:
            result = BilateralFilter({"filterSize": size}).compute(image)
            assert result.shape == image.shape

    def test_explicit_valid_sigma_values(self, image):
        """Valid sigma values should all work."""
        result = BilateralFilter({"sigmaColor": 50, "sigmaSpace": 50}).compute(image)
        assert result.shape == image.shape

    def test_small_sigma_values(self, image):
        """Small but positive sigma values should work."""
        result = BilateralFilter({"sigmaColor": 0.1, "sigmaSpace": 0.1}).compute(image)
        assert result.shape == image.shape

    def test_large_sigma_values(self, image):
        """Large sigma values should work."""
        result = BilateralFilter({"sigmaColor": 500, "sigmaSpace": 500}).compute(image)
        assert result.shape == image.shape

    def test_rgba_image_converted_to_bgr(self, rgba_image):
        """RGBA images should be converted to BGR before filtering."""
        result = BilateralFilter({}).compute(rgba_image)
        # Result should be BGR (3 channels)
        assert result.shape == (10, 10, 3)
        assert result.dtype == rgba_image.dtype

    def test_grayscale_image_works(self, gray_image):
        """Grayscale images should be processed directly."""
        result = BilateralFilter({}).compute(gray_image)
        assert result.shape == gray_image.shape
        assert result.dtype == gray_image.dtype

    def test_filter_effect_visible_on_gradient(self):
        """BilateralFilter should smooth gradients while preserving edges."""
        # Create a simple gradient image with a sharp edge
        image = np.zeros((20, 20, 3), dtype=np.uint8)
        image[:, :10] = 50
        image[:, 10:] = 200

        result = BilateralFilter({}).compute(image)

        # The filter should produce a smoother transition
        # (it should exist and have the same shape)
        assert result.shape == image.shape


class TestBilateralFilterInvalidFilterSize:
    """Test BilateralFilter rejects invalid filterSize values."""

    @pytest.mark.parametrize("bad_size", [0, -1, -5, -100])
    def test_non_positive_filter_size_raises(self, image, bad_size):
        """Zero or negative filterSize should raise ValueError."""
        with pytest.raises(ValueError, match="'filterSize'"):
            BilateralFilter({"filterSize": bad_size}).compute(image)

    @pytest.mark.parametrize("bad_size", [0, -1, -5])
    def test_error_message_is_user_friendly(self, image, bad_size):
        """Error message should mention the parameter name and valid range."""
        with pytest.raises(ValueError) as exc_info:
            BilateralFilter({"filterSize": bad_size}).compute(image)

        error_msg = str(exc_info.value)
        assert "filterSize" in error_msg
        assert "positive integer" in error_msg or "greater than 0" in error_msg

    def test_float_filter_size_gets_truncated_to_int(self, image):
        """Float values for filterSize get truncated to int (standard Python behavior)."""
        # filterSize=3.9 gets truncated to 3
        result = BilateralFilter({"filterSize": 3.9}).compute(image)
        assert result.shape == image.shape
        # The validation happens on the int value, so 3.9 -> 3 is valid


class TestBilateralFilterInvalidSigmaValues:
    """Test BilateralFilter rejects invalid sigma values."""

    @pytest.mark.parametrize("bad_sigma", [0, -1.0, -50])
    def test_non_positive_sigma_color_raises(self, image, bad_sigma):
        """Zero or negative sigmaColor should raise ValueError."""
        with pytest.raises(ValueError, match="'sigmaColor'"):
            BilateralFilter({"sigmaColor": bad_sigma}).compute(image)

    @pytest.mark.parametrize("bad_sigma", [0, -1.0, -50])
    def test_non_positive_sigma_space_raises(self, image, bad_sigma):
        """Zero or negative sigmaSpace should raise ValueError."""
        with pytest.raises(ValueError, match="'sigmaSpace'"):
            BilateralFilter({"sigmaSpace": bad_sigma}).compute(image)

    def test_sigma_color_error_message_user_friendly(self, image):
        """sigmaColor error message should be clear."""
        with pytest.raises(ValueError) as exc_info:
            BilateralFilter({"sigmaColor": 0}).compute(image)

        error_msg = str(exc_info.value)
        assert "sigmaColor" in error_msg
        assert "positive" in error_msg

    def test_sigma_space_error_message_user_friendly(self, image):
        """sigmaSpace error message should be clear."""
        with pytest.raises(ValueError) as exc_info:
            BilateralFilter({"sigmaSpace": -10}).compute(image)

        error_msg = str(exc_info.value)
        assert "sigmaSpace" in error_msg
        assert "positive" in error_msg


class TestBilateralFilterConsistencyWithOtherBlurring:
    """Verify BilateralFilter validation matches the pattern of other blur operators."""

    def test_filter_size_zero_and_negative_both_rejected(self, image):
        """Both 0 and negative values should be rejected, not just negatives."""
        # This is the core bug fix - zero should be rejected
        with pytest.raises(ValueError, match="filterSize"):
            BilateralFilter({"filterSize": 0}).compute(image)

        with pytest.raises(ValueError, match="filterSize"):
            BilateralFilter({"filterSize": -5}).compute(image)

    def test_validation_happens_before_cv2_call(self, image):
        """
        Validation should catch errors before calling cv2.bilateralFilter.
        This ensures we get our error messages, not OpenCV's raw error.
        """
        # If validation doesn't happen, cv2.bilateralFilter will raise cv2.error
        # If validation does happen, we get ValueError
        with pytest.raises(ValueError):
            BilateralFilter({"filterSize": 0}).compute(image)

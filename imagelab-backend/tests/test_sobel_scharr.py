import numpy as np
import pytest

from app.operators.sobel_derivatives.scharr_derivative import ScharrDerivative
from app.operators.sobel_derivatives.sobel_derivative import SobelDerivative

# Simple 8-bit grayscale test image with a vertical edge.
_GRAY = np.zeros((64, 64), dtype=np.uint8)
_GRAY[:, 32:] = 255

# BGRA image with a vertical edge (4-channel with alpha)
_BGRA = np.zeros((64, 64, 4), dtype=np.uint8)
_BGRA[:, 32:, 0] = 255  # blue channel edge
_BGRA[:, :, 3] = 128  # semi-transparent alpha

# 3-D single-channel image (H, W, 1)
_GRAY_1CH = np.zeros((64, 64, 1), dtype=np.uint8)
_GRAY_1CH[:, 32:, 0] = 255


class TestSobelDerivative:
    def test_horizontal_dtype_and_range(self):
        result = SobelDerivative({"type": "HORIZONTAL"}).compute(_GRAY)
        assert result.dtype == np.uint8
        assert result.min() >= 0 and result.max() <= 255

    def test_vertical_dtype_and_range(self):
        result = SobelDerivative({"type": "VERTICAL"}).compute(_GRAY)
        assert result.dtype == np.uint8
        assert result.min() >= 0 and result.max() <= 255

    def test_combined_dtype_and_range(self):
        result = SobelDerivative({"type": "BOTH"}).compute(_GRAY)
        assert result.dtype == np.uint8
        assert result.min() >= 0 and result.max() <= 255

    def test_grayscale_input(self):
        gray = np.random.randint(0, 256, (48, 48), dtype=np.uint8)
        result = SobelDerivative({"type": "HORIZONTAL"}).compute(gray)
        assert result.shape == gray.shape
        assert result.dtype == np.uint8

    def test_bgra_input_produces_single_channel_output(self):
        """BGRA images must be converted before Sobel — output should be 2D (grayscale), not 4-channel."""
        result = SobelDerivative({"type": "HORIZONTAL"}).compute(_BGRA)
        assert result.dtype == np.uint8
        assert result.ndim == 2, f"Expected 2D output for BGRA input, got shape {result.shape}"

    def test_bgra_vertical(self):
        result = SobelDerivative({"type": "VERTICAL"}).compute(_BGRA)
        assert result.dtype == np.uint8
        assert result.ndim == 2, f"Expected 2D output for BGRA input, got shape {result.shape}"

    def test_bgra_both(self):
        result = SobelDerivative({"type": "BOTH"}).compute(_BGRA)
        assert result.dtype == np.uint8
        assert result.ndim == 2, f"Expected 2D output for BGRA input, got shape {result.shape}"

    def test_single_channel_3d_input_horizontal(self):
        result = SobelDerivative({"type": "HORIZONTAL"}).compute(_GRAY_1CH)
        assert result.shape == (64, 64)
        assert result.dtype == np.uint8
        np.testing.assert_array_equal(result, SobelDerivative({"type": "HORIZONTAL"}).compute(_GRAY))

    def test_single_channel_3d_input_vertical(self):
        result = SobelDerivative({"type": "VERTICAL"}).compute(_GRAY_1CH)
        assert result.shape == (64, 64)
        assert result.dtype == np.uint8
        np.testing.assert_array_equal(result, SobelDerivative({"type": "VERTICAL"}).compute(_GRAY))

    def test_single_channel_3d_input_both(self):
        result = SobelDerivative({"type": "BOTH"}).compute(_GRAY_1CH)
        assert result.shape == (64, 64)
        assert result.dtype == np.uint8
        np.testing.assert_array_equal(result, SobelDerivative({"type": "BOTH"}).compute(_GRAY))

    def test_case_insensitive_direction(self):
        result_lower = SobelDerivative({"type": "horizontal"}).compute(_GRAY)
        result_upper = SobelDerivative({"type": "HORIZONTAL"}).compute(_GRAY)
        np.testing.assert_array_equal(result_lower, result_upper)

    def test_invalid_empty_image_raises_error(self):
        with pytest.raises(ValueError, match="invalid or empty image"):
            SobelDerivative({}).compute(np.array([], dtype=np.uint8))

    def test_none_image_raises_error(self):
        with pytest.raises(ValueError, match="invalid or empty image"):
            SobelDerivative({}).compute(None)

    def test_invalid_channels_raises_error(self):
        with pytest.raises(ValueError, match="expects 1, 3, or 4 channels"):
            SobelDerivative({}).compute(np.zeros((64, 64, 2), dtype=np.uint8))

    def test_invalid_dtype_raises_error(self):
        with pytest.raises(ValueError, match="expects a uint8 image"):
            SobelDerivative({}).compute(np.zeros((64, 64), dtype=np.float32))


class TestScharrDerivative:
    def test_horizontal_dtype_and_range(self):
        result = ScharrDerivative({"type": "HORIZONTAL"}).compute(_GRAY)
        assert result.dtype == np.uint8
        assert result.min() >= 0 and result.max() <= 255

    def test_vertical_dtype_and_range(self):
        result = ScharrDerivative({"type": "VERTICAL"}).compute(_GRAY)
        assert result.dtype == np.uint8
        assert result.min() >= 0 and result.max() <= 255

    def test_grayscale_input(self):
        gray = np.random.randint(0, 256, (48, 48), dtype=np.uint8)
        result = ScharrDerivative({"type": "HORIZONTAL"}).compute(gray)
        assert result.shape == gray.shape
        assert result.dtype == np.uint8

    def test_bgra_input_produces_single_channel_output(self):
        """BGRA images must be converted before Scharr — output should be 2D (grayscale), not 4-channel."""
        result = ScharrDerivative({"type": "HORIZONTAL"}).compute(_BGRA)
        assert result.dtype == np.uint8
        assert result.ndim == 2, f"Expected 2D output for BGRA input, got shape {result.shape}"

    def test_bgra_vertical(self):
        result = ScharrDerivative({"type": "VERTICAL"}).compute(_BGRA)
        assert result.dtype == np.uint8
        assert result.ndim == 2, f"Expected 2D output for BGRA input, got shape {result.shape}"

    def test_single_channel_3d_input(self):
        result = ScharrDerivative({"type": "HORIZONTAL"}).compute(_GRAY_1CH)
        assert result.shape == (64, 64)
        assert result.dtype == np.uint8
        np.testing.assert_array_equal(result, ScharrDerivative({"type": "HORIZONTAL"}).compute(_GRAY))

    def test_case_insensitive_direction(self):
        result_lower = ScharrDerivative({"type": "horizontal"}).compute(_GRAY)
        result_upper = ScharrDerivative({"type": "HORIZONTAL"}).compute(_GRAY)
        np.testing.assert_array_equal(result_lower, result_upper)

    def test_scharr_invalid_image_raises_error(self):
        with pytest.raises(ValueError, match="invalid or empty image"):
            ScharrDerivative({}).compute(None)

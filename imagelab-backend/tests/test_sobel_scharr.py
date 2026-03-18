import numpy as np

from app.operators.sobel_derivatives.scharr_derivative import ScharrDerivative
from app.operators.sobel_derivatives.sobel_derivative import SobelDerivative

# Simple 8-bit grayscale test image with a vertical edge.
_GRAY = np.zeros((64, 64), dtype=np.uint8)
_GRAY[:, 32:] = 255


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

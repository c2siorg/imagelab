import cv2
import numpy as np
import pytest

from app.operators.sobel_derivatives.sobel_derivative import SobelDerivative


def _sharp_edge_image() -> np.ndarray:
    """100x100 grayscale image with a vertical edge at column 50."""
    img = np.zeros((100, 100), dtype=np.uint8)
    img[:, 50:] = 255
    return img


def test_sobel_horizontal_returns_uint8() -> None:
    result = SobelDerivative({"type": "HORIZONTAL"}).compute(_sharp_edge_image())
    assert result.dtype == np.uint8


def test_sobel_vertical_returns_uint8() -> None:
    result = SobelDerivative({"type": "VERTICAL"}).compute(_sharp_edge_image())
    assert result.dtype == np.uint8


def test_sobel_both_returns_uint8() -> None:
    result = SobelDerivative({"type": "BOTH"}).compute(_sharp_edge_image())
    assert result.dtype == np.uint8


def test_sobel_output_is_png_encodable() -> None:
    result = SobelDerivative({"type": "HORIZONTAL"}).compute(_sharp_edge_image())
    success, _ = cv2.imencode(".png", result)
    assert success, "Sobel output must be PNG-encodable"


def test_sobel_no_overflow_on_sharp_edge() -> None:
    """convertScaleAbs must produce a strong (near-255) response at the edge, not a wrapped low value."""
    result = SobelDerivative({"type": "HORIZONTAL"}).compute(_sharp_edge_image())
    assert result.max() > 200, f"Expected strong edge response, got max={result.max()}"


def test_sobel_both_uses_l2_magnitude() -> None:
    """BOTH direction should use np.hypot (L2 norm), not arithmetic mean."""
    img = np.zeros((50, 50), dtype=np.uint8)
    img[10:40, 10:40] = 255  # square produces edges in both x and y
    result = SobelDerivative({"type": "BOTH"}).compute(img)
    assert result.dtype == np.uint8
    # L2 magnitude of a diagonal edge is stronger than either axis alone
    h_result = SobelDerivative({"type": "HORIZONTAL"}).compute(img)
    assert result.max() >= h_result.max()


@pytest.mark.parametrize("direction", ["HORIZONTAL", "VERTICAL", "BOTH"])
def test_sobel_output_shape_matches_input(direction: str) -> None:
    result = SobelDerivative({"type": direction}).compute(_sharp_edge_image())
    assert result.shape == _sharp_edge_image().shape

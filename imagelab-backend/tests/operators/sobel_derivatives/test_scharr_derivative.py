import cv2
import numpy as np
import pytest

from app.operators.sobel_derivatives.scharr_derivative import ScharrDerivative


def _sharp_edge_image() -> np.ndarray:
    """100x100 grayscale image with a vertical edge at column 50."""
    img = np.zeros((100, 100), dtype=np.uint8)
    img[:, 50:] = 255
    return img


def test_scharr_horizontal_returns_uint8() -> None:
    result = ScharrDerivative({"type": "HORIZONTAL"}).compute(_sharp_edge_image())
    assert result.dtype == np.uint8


def test_scharr_vertical_returns_uint8() -> None:
    result = ScharrDerivative({"type": "VERTICAL"}).compute(_sharp_edge_image())
    assert result.dtype == np.uint8


def test_scharr_output_is_png_encodable() -> None:
    """Regression test: float64 output from cv2.Scharr used to crash cv2.imencode."""
    result = ScharrDerivative({"type": "HORIZONTAL"}).compute(_sharp_edge_image())
    success, _ = cv2.imencode(".png", result)
    assert success, "Scharr output must be PNG-encodable"


def test_scharr_no_overflow_on_sharp_edge() -> None:
    """convertScaleAbs must saturate correctly — strong edges should be near 255."""
    result = ScharrDerivative({"type": "HORIZONTAL"}).compute(_sharp_edge_image())
    assert result.max() > 200, f"Expected strong edge response, got max={result.max()}"


@pytest.mark.parametrize("direction", ["HORIZONTAL", "VERTICAL"])
def test_scharr_output_shape_matches_input(direction: str) -> None:
    result = ScharrDerivative({"type": direction}).compute(_sharp_edge_image())
    assert result.shape == _sharp_edge_image().shape

import numpy as np
import pytest

from app.operators.geometric.resize_image import ResizeImage


def test_resize_explicit_dimensions():
    # 10x10 image (height=10, width=10)
    image = np.zeros((10, 10, 3), dtype=np.uint8)

    op = ResizeImage(params={"width": 20, "height": 30, "interpolation": "LINEAR"})

    result = op.compute(image)
    assert result.shape == (30, 20, 3), "Image should be resized to w=20, h=30 (producing shape 30x20x3)"


def test_resize_noop_missing_params():
    image = np.zeros((15, 25, 3), dtype=np.uint8)

    op = ResizeImage(params={})

    result = op.compute(image)
    assert result.shape == (15, 25, 3), "Missing parameters should result in original dimensions (no-op)"


def test_resize_invalid_params():
    image = np.zeros((15, 25, 3), dtype=np.uint8)

    op = ResizeImage(params={"width": -5, "height": 40})

    result = op.compute(image)
    assert result.shape == (40, 25, 3), "Invalid axis parameters should independently fallback to original length"


def test_resize_interpolation_methods():
    image = np.zeros((10, 10, 3), dtype=np.uint8)

    for method in ["LINEAR", "AREA", "CUBIC", "NEAREST", "LANCZOS4"]:
        op = ResizeImage(params={"width": 15, "height": 15, "interpolation": method})
        try:
            result = op.compute(image)
            assert result.shape == (15, 15, 3), f"{method} interpolation produced incorrect shape"
        except Exception as e:
            pytest.fail(f"Interpolation {method} threw an exception: {e}")

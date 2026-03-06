import numpy as np

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
        result = op.compute(image)
        assert result.shape == (15, 15, 3), f"{method} interpolation produced incorrect shape"


def test_resize_zero_dimension_fallback():
    image = np.zeros((15, 25, 3), dtype=np.uint8)

    op = ResizeImage(params={"width": 0, "height": 0})

    result = op.compute(image)
    assert result.shape == (15, 25, 3), "Zero dimensions should fall back to original"


def test_resize_partial_zero_dimension():
    image = np.zeros((15, 25, 3), dtype=np.uint8)

    op = ResizeImage(params={"width": 0, "height": 30})

    result = op.compute(image)
    assert result.shape == (30, 25, 3), "Zero width falls back; valid height applies"


def test_resize_unknown_interpolation_defaults_to_linear():
    image = np.zeros((10, 10, 3), dtype=np.uint8)

    op = ResizeImage(params={"width": 20, "height": 20, "interpolation": "BILINEAR"})

    result = op.compute(image)  # Should not raise; falls back to LINEAR
    assert result.shape == (20, 20, 3)


def test_resize_grayscale_image():
    image = np.zeros((10, 10), dtype=np.uint8)  # 2D grayscale

    op = ResizeImage(params={"width": 20, "height": 30})

    result = op.compute(image)
    assert result.shape == (30, 20), "Grayscale image should resize correctly"

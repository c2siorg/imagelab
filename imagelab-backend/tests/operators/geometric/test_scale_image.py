import numpy as np
import pytest

from app.operators.geometric.scale_image import ScaleImage


@pytest.mark.parametrize(
    "fx,fy,shape",
    [
        (1.0, 1.0, (10, 20, 3)),
        (2.0, 2.0, (20, 40, 3)),
        (0.5, 0.5, (5, 10, 3)),
        (1.5, 2.0, (20, 30, 3)),
        (0.25, 3.0, (30, 5, 3)),
    ],
)
def test_scale_output_dimensions(fx: float, fy: float, shape: tuple[int, int, int]) -> None:
    img = np.zeros((10, 20, 3), dtype=np.uint8)
    out = ScaleImage({"fx": fx, "fy": fy}).compute(img)
    assert out.shape == shape


def test_scale_identity_preserves_values() -> None:
    img = np.full((8, 12, 3), 123, dtype=np.uint8)
    out = ScaleImage({"fx": 1.0, "fy": 1.0}).compute(img)
    assert out.shape == img.shape
    assert np.array_equal(out, img)


def test_scale_constant_image_stays_constant() -> None:
    img = np.full((7, 9, 3), 7, dtype=np.uint8)
    out = ScaleImage({"fx": 2.0, "fy": 3.0}).compute(img)
    assert out.shape == (21, 18, 3)
    assert np.all(out == 7)


def test_scale_missing_parameters_uses_defaults() -> None:
    # ScaleImage defaults: fx=1, fy=1 — output shape equals input shape
    img = np.zeros((10, 20, 3), dtype=np.uint8)
    out = ScaleImage({}).compute(img)
    assert out.shape == img.shape

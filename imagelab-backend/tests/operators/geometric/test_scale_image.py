import numpy as np
import pytest

from app.operators.geometric.scale_image import ScaleImage


def test_scale_image_uses_default_factors_of_one() -> None:
    """ScaleImage({}) with no params defaults fx=1, fy=1 — output shape equals input."""
    image = np.zeros((10, 20, 3), dtype=np.uint8)
    out = ScaleImage({}).compute(image)
    assert out.shape == image.shape


def test_scale_image_resizes_with_positive_factors() -> None:
    image = np.zeros((10, 20, 3), dtype=np.uint8)

    out = ScaleImage({"fx": 1.5, "fy": 0.5}).compute(image)

    assert out.shape == (5, 30, 3)


@pytest.mark.parametrize(
    ("fx", "fy"),
    [
        (0, 1),
        (1, 0),
        (-1, 1),
        (1, -1),
        (0, 0),
        (-1, -1),
        (float("nan"), 1),
        (1, float("nan")),
        (float("inf"), 1),
        (1, float("inf")),
    ],
)
def test_scale_image_rejects_invalid_scale_factors(fx: float, fy: float) -> None:
    image = np.zeros((10, 10, 3), dtype=np.uint8)

    with pytest.raises(ValueError):
        ScaleImage({"fx": fx, "fy": fy}).compute(image)

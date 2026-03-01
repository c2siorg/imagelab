import numpy as np
import pytest

from app.operators.geometric.scale_image import ScaleImage


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
    ],
)
def test_scale_image_rejects_non_positive_scale_factors(fx: float, fy: float) -> None:
    image = np.zeros((10, 10, 3), dtype=np.uint8)

    with pytest.raises(ValueError, match="fx and fy must be greater than 0"):
        ScaleImage({"fx": fx, "fy": fy}).compute(image)

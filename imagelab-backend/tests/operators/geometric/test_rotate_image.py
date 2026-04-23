import numpy as np
import pytest

from app.operators.geometric.rotate_image import RotateImage


def test_rotate_image_default_params() -> None:
    image = np.zeros((100, 100, 3), dtype=np.uint8)
    out = RotateImage({}).compute(image)
    assert out.shape == image.shape


def test_rotate_image_preserves_shape() -> None:
    image = np.zeros((60, 80, 3), dtype=np.uint8)
    out = RotateImage({"angle": 45, "scale": 1.0}).compute(image)
    assert out.shape == image.shape


@pytest.mark.parametrize("scale", [0, -1, -0.5, float("inf"), float("-inf"), float("nan")])
def test_rotate_image_rejects_invalid_scale(scale: float) -> None:
    image = np.zeros((10, 10, 3), dtype=np.uint8)
    with pytest.raises(ValueError):
        RotateImage({"scale": scale}).compute(image)


def test_rotate_image_positive_scale_works() -> None:
    image = np.zeros((10, 10, 3), dtype=np.uint8)
    out = RotateImage({"angle": 90, "scale": 0.5}).compute(image)
    assert out.shape == image.shape

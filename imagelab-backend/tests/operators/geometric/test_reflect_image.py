import numpy as np
import pytest

from app.operators.geometric.reflect_image import ReflectImage


@pytest.mark.parametrize(
    "flip_type,expected",
    [
        ("X", np.array([[3, 4, 5], [0, 1, 2]], dtype=np.uint8)),
        ("Y", np.array([[2, 1, 0], [5, 4, 3]], dtype=np.uint8)),
        ("Both", np.array([[5, 4, 3], [2, 1, 0]], dtype=np.uint8)),
        ("UNKNOWN", np.array([[3, 4, 5], [0, 1, 2]], dtype=np.uint8)),
    ],
)
def test_reflect_flip_modes(flip_type: str, expected: np.ndarray) -> None:
    img = np.array([[0, 1, 2], [3, 4, 5]], dtype=np.uint8)
    out = ReflectImage({"type": flip_type}).compute(img)
    assert np.array_equal(out, expected)


def test_reflect_preserves_shape() -> None:
    img = np.zeros((10, 20, 3), dtype=np.uint8)
    out = ReflectImage({"type": "Y"}).compute(img)
    assert out.shape == img.shape

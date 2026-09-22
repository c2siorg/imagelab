import numpy as np

from app.operators.geometric.reflect_image import ReflectImage


def _single_bright_pixel(rows: int = 60, cols: int = 100, x: int = 20, y: int = 10) -> np.ndarray:
    image = np.zeros((rows, cols), dtype=np.uint8)
    image[y, x] = 255
    return image


def _bright_pixel_position(image: np.ndarray) -> tuple[int, int]:
    ys, xs = np.where(image == 255)
    assert len(ys) == 1
    return int(ys[0]), int(xs[0])


def test_default_type_flips_around_x_axis():
    image = _single_bright_pixel()
    result = ReflectImage({}).compute(image)
    np.testing.assert_array_equal(result, ReflectImage({"type": "X"}).compute(image))
    assert _bright_pixel_position(result) == (49, 20)


def test_type_x_flips_rows():
    image = _single_bright_pixel(x=20, y=10)
    result = ReflectImage({"type": "X"}).compute(image)
    assert result.shape == image.shape
    assert _bright_pixel_position(result) == (49, 20)


def test_type_y_flips_columns():
    image = _single_bright_pixel(x=20, y=10)
    result = ReflectImage({"type": "Y"}).compute(image)
    assert result.shape == image.shape
    assert _bright_pixel_position(result) == (10, 79)


def test_type_both_flips_rows_and_columns():
    image = _single_bright_pixel(x=20, y=10)
    result = ReflectImage({"type": "Both"}).compute(image)
    assert result.shape == image.shape
    assert _bright_pixel_position(result) == (49, 79)


def test_unknown_type_falls_back_to_x_axis_flip():
    image = _single_bright_pixel(x=20, y=10)
    result = ReflectImage({"type": "Diagonal"}).compute(image)
    assert _bright_pixel_position(result) == (49, 20)


def test_non_square_image_keeps_orientation():
    image = _single_bright_pixel(rows=30, cols=90, x=5, y=2)
    for flip_type in ("X", "Y", "Both"):
        result = ReflectImage({"type": flip_type}).compute(image)
        assert result.shape == (30, 90)
    assert _bright_pixel_position(ReflectImage({"type": "X"}).compute(image)) == (27, 5)
    assert _bright_pixel_position(ReflectImage({"type": "Y"}).compute(image)) == (2, 84)
    assert _bright_pixel_position(ReflectImage({"type": "Both"}).compute(image)) == (27, 84)

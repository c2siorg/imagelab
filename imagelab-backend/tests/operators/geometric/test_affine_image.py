import numpy as np

from app.operators.geometric.affine_image import AffineImage


def _single_bright_pixel(rows: int = 80, cols: int = 80, x: int = 20, y: int = 30) -> np.ndarray:
    image = np.zeros((rows, cols), dtype=np.uint8)
    image[y, x] = 255
    return image


def test_default_params_are_identity_translation():
    image = _single_bright_pixel()
    result = AffineImage({}).compute(image)
    np.testing.assert_array_equal(result, image)


def test_translation_moves_bright_pixel_by_exact_offset():
    image = _single_bright_pixel(x=20, y=30)
    result = AffineImage({"translate_x": 15, "translate_y": 25}).compute(image)
    ys, xs = np.where(result == 255)
    assert (int(ys[0]), int(xs[0])) == (55, 35)


def test_negative_translation_is_supported():
    image = _single_bright_pixel(x=40, y=40)
    result = AffineImage({"translate_x": -10, "translate_y": -5}).compute(image)
    ys, xs = np.where(result == 255)
    assert (int(ys[0]), int(xs[0])) == (35, 30)


def test_translation_out_of_frame_clips_to_zero():
    image = _single_bright_pixel(x=10, y=10)
    result = AffineImage({"translate_x": 200, "translate_y": 200}).compute(image)
    assert result.max() == 0

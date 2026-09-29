import numpy as np

from app.operators.geometric.affine_image import AffineImage


def _single_bright_pixel(rows: int = 80, cols: int = 80, x: int = 20, y: int = 30) -> np.ndarray:
    image = np.zeros((rows, cols), dtype=np.uint8)
    image[y, x] = 255
    return image


def _points(prefix: str, *coords: tuple[float, float]) -> dict:
    params = {}
    for i, (x, y) in enumerate(coords, 1):
        params[f"{prefix}_x{i}"] = x
        params[f"{prefix}_y{i}"] = y
    return params


def _bright_pixel_position(result: np.ndarray) -> tuple[int, int]:
    ys, xs = np.where(result == 255)
    assert len(ys) == 1
    return int(ys[0]), int(xs[0])


def test_default_params_are_identity_translation():
    image = _single_bright_pixel()
    result = AffineImage({}).compute(image)
    np.testing.assert_array_equal(result, image)


def test_default_params_are_identity_on_non_square_image():
    image = _single_bright_pixel(rows=50, cols=120, x=100, y=7)
    result = AffineImage({}).compute(image)
    np.testing.assert_array_equal(result, image)


def test_matching_source_and_destination_points_is_identity():
    image = _single_bright_pixel()
    params = {**_points("src", (10, 10), (60, 10), (10, 60)), **_points("dst", (10, 10), (60, 10), (10, 60))}
    result = AffineImage(params).compute(image)
    np.testing.assert_array_equal(result, image)


def test_shifted_destination_points_translate_image():
    image = _single_bright_pixel(x=20, y=30)
    params = {**_points("src", (0, 0), (10, 0), (0, 10)), **_points("dst", (15, 25), (25, 25), (15, 35))}
    result = AffineImage(params).compute(image)
    assert _bright_pixel_position(result) == (55, 35)


def test_moving_one_destination_point_shears_image():
    image = _single_bright_pixel(x=20, y=30)
    # x' = x + 0.5 * y, y' = y
    params = {**_points("src", (0, 0), (10, 0), (0, 10)), **_points("dst", (0, 0), (10, 0), (5, 10))}
    result = AffineImage(params).compute(image)
    assert _bright_pixel_position(result) == (30, 35)


def test_spreading_destination_points_scales_image():
    image = _single_bright_pixel(x=20, y=30)
    params = {**_points("src", (0, 0), (10, 0), (0, 10)), **_points("dst", (0, 0), (20, 0), (0, 20))}
    result = AffineImage(params).compute(image)
    assert result[60, 40] == 255
    assert np.unravel_index(result.argmax(), result.shape) == (60, 40)


def test_points_work_on_color_image():
    image = np.zeros((80, 80, 3), dtype=np.uint8)
    image[30, 20] = (10, 20, 255)
    params = {**_points("src", (0, 0), (10, 0), (0, 10)), **_points("dst", (5, 5), (15, 5), (5, 15))}
    result = AffineImage(params).compute(image)
    assert result.shape == image.shape
    assert tuple(result[35, 25]) == (10, 20, 255)


def test_collinear_source_points_return_image_unchanged():
    image = _single_bright_pixel()
    params = {**_points("src", (0, 0), (10, 10), (20, 20)), **_points("dst", (0, 0), (10, 0), (0, 10))}
    result = AffineImage(params).compute(image)
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

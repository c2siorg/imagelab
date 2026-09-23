import numpy as np
import pytest

from app.operators.geometric.crop_image import CropImage


def _rgb_image() -> np.ndarray:
    return np.arange(5 * 6 * 3, dtype=np.uint8).reshape(5, 6, 3)


def test_crop_inside_image_returns_exact_slice() -> None:
    image = _rgb_image()

    result = CropImage({"x1": 1, "y1": 2, "x2": 5, "y2": 5}).compute(image)

    assert result.shape == (3, 4, 3)
    np.testing.assert_array_equal(result, image[2:5, 1:5])


def test_out_of_bounds_coordinates_are_clamped() -> None:
    image = _rgb_image()

    result = CropImage({"x1": -3, "y1": -2, "x2": 99, "y2": 3}).compute(image)

    assert result.shape == (3, 6, 3)
    np.testing.assert_array_equal(result, image[:3, :])


@pytest.mark.parametrize(
    "params",
    [
        {"x1": 2, "x2": 2},
        {"x1": 4, "x2": 1},
        {"y1": 3, "y2": 3},
        {"y1": 4, "y2": 1},
        {"x1": 0, "y1": 0, "x2": 0, "y2": 0},
        {"x1": 50, "y1": 0, "x2": 60, "y2": 5},
    ],
)
def test_empty_or_inverted_box_raises_value_error(params: dict[str, int]) -> None:
    image = _rgb_image()

    with pytest.raises(ValueError, match="crop rectangle"):
        CropImage(params).compute(image)


def test_error_message_reports_requested_rectangle_and_image_size() -> None:
    image = _rgb_image()

    with pytest.raises(ValueError, match=r"x1=50, y1=0, x2=60, y2=5 is empty for a 6x5 image"):
        CropImage({"x1": 50, "y1": 0, "x2": 60, "y2": 5}).compute(image)


def test_block_default_rectangle_crops_top_left_region() -> None:
    # Defaults shipped by the Crop block in the frontend (geometric.blocks.ts).
    image = np.zeros((480, 640, 3), dtype=np.uint8)

    result = CropImage({"x1": 0, "y1": 0, "x2": 320, "y2": 240}).compute(image)

    assert result.shape == (240, 320, 3)


def test_default_parameters_return_full_single_channel_image() -> None:
    image = np.arange(5 * 6, dtype=np.uint8).reshape(5, 6)

    result = CropImage({}).compute(image)

    assert result.shape == image.shape
    np.testing.assert_array_equal(result, image)

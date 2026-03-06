import cv2
import numpy as np
import pytest

from app.operators.filtering.box_filter import BoxFilter


def test_box_filter_uses_width_height_kernel_order() -> None:
    """Regression test for #125: kernel was applied as (height, width) instead of (width, height).
    An asymmetric kernel (width=3, height=5) is used so the two orderings produce different output,
    making the test sensitive to the exact bug it guards against.
    """
    image = np.arange(8 * 9, dtype=np.uint8).reshape(8, 9)

    box_filter = BoxFilter({"width": 3, "height": 5, "depth": -1, "point_x": -1, "point_y": -1})
    out = box_filter.compute(image)

    correct_expected = cv2.boxFilter(image, -1, (3, 5), anchor=(-1, -1), normalize=True, borderType=cv2.BORDER_DEFAULT)
    swapped_expected = cv2.boxFilter(image, -1, (5, 3), anchor=(-1, -1), normalize=True, borderType=cv2.BORDER_DEFAULT)

    # Sanity check: the two orderings must differ so this test is meaningful
    assert not np.array_equal(correct_expected, swapped_expected)
    assert np.array_equal(out, correct_expected)


def test_box_filter_uniform_image_is_unchanged() -> None:
    """Box filter on a uniform image should return the same pixel values."""
    image = np.full((10, 10), 128, dtype=np.uint8)
    box_filter = BoxFilter({"width": 3, "height": 3, "depth": -1, "point_x": -1, "point_y": -1})
    out = box_filter.compute(image)
    assert np.all(out == 128)


@pytest.mark.parametrize("width,height", [(3, 3), (3, 5), (5, 3), (1, 7)])
def test_box_filter_kernel_shapes(width: int, height: int) -> None:
    """BoxFilter output matches cv2.boxFilter for various kernel dimensions."""
    image = np.random.randint(0, 256, (20, 20), dtype=np.uint8)
    box_filter = BoxFilter({"width": width, "height": height, "depth": -1, "point_x": -1, "point_y": -1})
    out = box_filter.compute(image)
    expected = cv2.boxFilter(
        image,
        -1,
        (width, height),
        anchor=(-1, -1),
        normalize=True,
        borderType=cv2.BORDER_DEFAULT,
    )
    assert np.array_equal(out, expected)

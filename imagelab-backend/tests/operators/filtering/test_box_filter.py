import cv2
import numpy as np

from app.operators.filtering.box_filter import BoxFilter


def test_box_filter_uses_width_height_kernel_order() -> None:
    image = np.arange(8 * 9, dtype=np.uint8).reshape(8, 9)

    out = BoxFilter({"width": 3, "height": 5, "depth": -1, "point_x": -1, "point_y": -1}).compute(image)
    expected = cv2.boxFilter(
        image,
        -1,
        (3, 5),
        anchor=(-1, -1),
        normalize=True,
        borderType=cv2.BORDER_DEFAULT,
    )

    assert np.array_equal(out, expected)

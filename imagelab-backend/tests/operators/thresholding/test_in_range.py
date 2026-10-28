import re

import cv2
import numpy as np
import pytest

from app.operators.registry import get_operator
from app.operators.thresholding.in_range import InRangeThreshold


def test_in_range_is_registered():
    assert get_operator("thresholding_inrange") is InRangeThreshold


def test_in_range_grayscale_mask():
    image = np.array([[50, 100, 150], [20, 120, 200]], dtype=np.uint8)
    op = InRangeThreshold({"lower1": 80, "upper1": 130, "outputMode": "mask"})
    mask = op.compute(image)
    assert mask.shape == (2, 3) and mask.dtype == np.uint8
    np.testing.assert_array_equal(mask, np.array([[0, 255, 0], [0, 255, 0]], dtype=np.uint8))


def test_in_range_grayscale_masked_image():
    image = np.array([[50, 100], [120, 200]], dtype=np.uint8)
    op = InRangeThreshold({"lower1": 80, "upper1": 150, "outputMode": "masked_image"})
    result = op.compute(image)
    assert result.shape == (2, 2) and result.dtype == np.uint8
    np.testing.assert_array_equal(result, np.array([[0, 100], [120, 0]], dtype=np.uint8))


def test_in_range_grayscale_3d():
    image = np.array([[[50], [100]], [[120], [200]]], dtype=np.uint8)
    mask = InRangeThreshold({"lower1": 80, "upper1": 150, "outputMode": "mask"}).compute(image)
    assert mask.shape == (2, 2)
    result = InRangeThreshold({"lower1": 80, "upper1": 150, "outputMode": "masked_image"}).compute(image)
    assert result.shape == (2, 2, 1) and result[0, 1, 0] == 100 and result[0, 0, 0] == 0


def test_in_range_bgr_mask_and_masked_image():
    image = np.zeros((2, 2, 3), dtype=np.uint8)
    image[0, 0] = [10, 20, 30]
    image[0, 1] = [100, 150, 200]
    image[1, 0] = [50, 50, 50]
    image[1, 1] = [120, 160, 210]

    bounds = {"lower1": 90, "upper1": 130, "lower2": 140, "upper2": 170, "lower3": 190, "upper3": 220}
    mask = InRangeThreshold({**bounds, "outputMode": "mask"}).compute(image)
    assert mask.shape == (2, 2) and mask[0, 0] == 0 and mask[0, 1] == 255 and mask[1, 1] == 255

    masked = InRangeThreshold({**bounds, "outputMode": "masked_image"}).compute(image)
    assert masked.shape == (2, 2, 3)
    np.testing.assert_array_equal(masked[0, 0], [0, 0, 0])
    np.testing.assert_array_equal(masked[0, 1], [100, 150, 200])


def test_in_range_bgra():
    image = np.zeros((2, 2, 4), dtype=np.uint8)
    image[0, 0] = [20, 30, 40, 255]
    image[0, 1] = [100, 100, 100, 180]

    params = {"lower1": 90, "upper1": 110, "lower2": 90, "upper2": 110, "lower3": 90, "upper3": 110}
    mask = InRangeThreshold({**params, "outputMode": "mask"}).compute(image)
    assert mask.shape == (2, 2) and mask[0, 0] == 0 and mask[0, 1] == 255

    result = InRangeThreshold({**params, "outputMode": "masked_image"}).compute(image)
    assert result.shape == (2, 2, 4)
    np.testing.assert_array_equal(result[0, 0], [0, 0, 0, 0])
    np.testing.assert_array_equal(result[0, 1], [100, 100, 100, 180])


def test_full_range_and_disjoint_range():
    image = np.full((10, 10, 3), 100, dtype=np.uint8)
    full_p = {"lower1": 0, "upper1": 255, "lower2": 0, "upper2": 255, "lower3": 0, "upper3": 255}
    assert (InRangeThreshold({**full_p, "outputMode": "mask"}).compute(image) == 255).all()

    disjoint_p = {"lower1": 0, "upper1": 50, "lower2": 0, "upper2": 50, "lower3": 0, "upper3": 50}
    assert (InRangeThreshold({**disjoint_p, "outputMode": "mask"}).compute(image) == 0).all()


def test_hsv_color_segmentation():
    bgr = np.zeros((20, 20, 3), dtype=np.uint8)
    bgr[:10, :] = [255, 0, 0]  # Blue patch
    bgr[10:, :] = [0, 0, 255]  # Red patch

    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    params = {"lower1": 100, "upper1": 140, "lower2": 150, "upper2": 255, "lower3": 150, "upper3": 255}
    mask = InRangeThreshold({**params, "outputMode": "mask"}).compute(hsv)
    assert (mask[:10, :] == 255).all() and (mask[10:, :] == 0).all()


def test_invalid_output_mode_raises():
    with pytest.raises(ValueError, match="Invalid outputMode 'invalid'"):
        InRangeThreshold({"outputMode": "invalid"})


@pytest.mark.parametrize(
    "params,err_msg",
    [
        ({"lower1": 200, "upper1": 100}, "lower1 (200) cannot exceed upper1 (100)"),
        ({"lower2": 150, "upper2": 50}, "lower2 (150) cannot exceed upper2 (50)"),
        ({"lower3": 250, "upper3": 10}, "lower3 (250) cannot exceed upper3 (10)"),
    ],
)
def test_lower_greater_than_upper_raises(params, err_msg):
    with pytest.raises(ValueError, match=re.escape(err_msg)):
        InRangeThreshold(params)


@pytest.mark.parametrize("key,val", [("lower1", "abc"), ("lower1", True), ("upper2", None)])
def test_invalid_bound_types_raise(key, val):
    with pytest.raises(ValueError):
        InRangeThreshold({key: val})


def test_bound_clamping():
    op = InRangeThreshold({"lower1": -50, "upper1": 350})
    assert op.lower1 == 0 and op.upper1 == 255


def test_empty_or_none_image_raises():
    op = InRangeThreshold({})
    with pytest.raises(ValueError, match="Input image cannot be empty or None"):
        op.compute(None)
    with pytest.raises(ValueError, match="Input image cannot be empty or None"):
        op.compute(np.array([], dtype=np.uint8))

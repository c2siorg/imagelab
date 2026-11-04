import cv2
import numpy as np
import pytest

from app.operators.augmentation.sepia_filter import SepiaFilter
from app.operators.conversions.color_maps import ColorMaps
from app.operators.conversions.gray_to_binary import GrayToBinary
from app.operators.filtering.canny_edge import CannyEdge
from app.operators.filtering.gabor_filter import GaborFilter
from app.operators.filtering.laplacian import Laplacian as FilteringLaplacian
from app.operators.thresholding.adaptive_threshold import AdaptiveThreshold
from app.operators.thresholding.otsu_threshold import OtsuThreshold
from app.operators.transformation.distance_transform import DistanceTransform


@pytest.fixture
def gray_2d():
    img = np.zeros((64, 64), dtype=np.uint8)
    cv2.circle(img, (32, 32), 16, 255, -1)
    return img


@pytest.fixture
def gray_3d_1ch(gray_2d):
    return gray_2d[:, :, np.newaxis]


def test_canny_edge_1ch_3d(gray_2d, gray_3d_1ch):
    op = CannyEdge({"threshold1": 50, "threshold2": 150})
    res_2d = op.compute(gray_2d)
    res_3d = op.compute(gray_3d_1ch)
    assert res_3d.shape == (64, 64, 3)
    np.testing.assert_array_equal(res_2d, res_3d)


def test_adaptive_threshold_1ch_3d(gray_2d, gray_3d_1ch):
    op = AdaptiveThreshold({"maxValue": 255, "blockSize": 5, "cValue": 2})
    res_2d = op.compute(gray_2d)
    res_3d = op.compute(gray_3d_1ch)
    assert res_3d.shape == (64, 64)
    np.testing.assert_array_equal(res_2d, res_3d)


def test_otsu_threshold_1ch_3d(gray_2d, gray_3d_1ch):
    op = OtsuThreshold({"maxValue": 255})
    res_2d = op.compute(gray_2d)
    res_3d = op.compute(gray_3d_1ch)
    assert res_3d.shape == (64, 64)
    np.testing.assert_array_equal(res_2d, res_3d)


def test_color_maps_1ch_3d(gray_2d, gray_3d_1ch):
    op = ColorMaps({"type": "HOT"})
    res_2d = op.compute(gray_2d)
    res_3d = op.compute(gray_3d_1ch)
    assert res_3d.shape == (64, 64, 3)
    np.testing.assert_array_equal(res_2d, res_3d)


def test_gray_to_binary_1ch_3d(gray_2d, gray_3d_1ch):
    op = GrayToBinary({"thresholdValue": 128, "maxValue": 255})
    res_2d = op.compute(gray_2d)
    res_3d = op.compute(gray_3d_1ch)
    assert res_3d.shape == (64, 64)
    np.testing.assert_array_equal(res_2d, res_3d)


def test_distance_transform_1ch_3d(gray_2d, gray_3d_1ch):
    op = DistanceTransform({"type": "DIST_L2", "maskSize": 5})
    res_2d = op.compute(gray_2d)
    res_3d = op.compute(gray_3d_1ch)
    assert res_3d.shape == (64, 64)
    np.testing.assert_array_equal(res_2d, res_3d)


def test_gabor_filter_1ch_3d(gray_2d, gray_3d_1ch):
    op = GaborFilter({"kernelSize": 9, "sigma": 2.0, "theta": 0.0, "lambda_": 5.0, "gamma": 0.5})
    res_2d = op.compute(gray_2d)
    res_3d = op.compute(gray_3d_1ch)
    assert res_3d.shape == (64, 64, 3)
    np.testing.assert_array_equal(res_2d, res_3d)


def test_laplacian_1ch_3d(gray_2d, gray_3d_1ch):
    op = FilteringLaplacian({"ksize": 3})
    res_2d = op.compute(gray_2d)
    res_3d = op.compute(gray_3d_1ch)
    assert res_3d.shape == (64, 64)
    np.testing.assert_array_equal(res_2d, res_3d)


def test_sepia_filter_1ch_3d(gray_2d, gray_3d_1ch):
    op = SepiaFilter({"intensity": 0.8})
    res_2d = op.compute(gray_2d)
    res_3d = op.compute(gray_3d_1ch)
    assert res_3d.shape == (64, 64, 3)
    np.testing.assert_array_equal(res_2d, res_3d)


@pytest.mark.parametrize(
    "op_type,params",
    [
        ("filtering_cannyedge", {"threshold1": 50, "threshold2": 150}),
        ("thresholding_adaptivethreshold", {"maxValue": 255, "blockSize": 5, "cValue": 2}),
        ("thresholding_otsuthreshold", {"maxValue": 255}),
        ("imageconversions_colormaps", {"type": "HOT"}),
        ("imageconversions_graytobinary", {"thresholdValue": 128, "maxValue": 255}),
        ("transformation_distance", {"type": "DIST_L2", "maskSize": 5}),
        ("augmentation_sepiafilter", {"intensity": 0.8}),
    ],
)
def test_exported_code_runs_on_1ch_3d_input(op_type, params, gray_3d_1ch):
    from app.services.python_exporter.templates import OPERATOR_TEMPLATES

    template_fn = OPERATOR_TEMPLATES[op_type]
    code_lines, _ = template_fn(params, "img")
    exec_scope = {"cv2": cv2, "np": np, "img": gray_3d_1ch.copy()}
    exec("\n".join(code_lines), exec_scope)
    out = exec_scope["img"]
    assert isinstance(out, np.ndarray)
    assert out.size > 0

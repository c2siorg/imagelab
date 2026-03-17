import numpy as np
import pytest

from app.operators.sobel_derivatives.roberts_cross import RobertsCross


@pytest.fixture
def op():
    return RobertsCross(params={})


class TestRobertsCrossOutputShape:
    def test_grayscale_2d(self, op):
        img = np.zeros((10, 10), dtype=np.uint8)
        out = op.compute(img)
        assert out.shape == (10, 10)
        assert out.dtype == np.uint8

    def test_bgr_3channel(self, op):
        img = np.zeros((10, 10, 3), dtype=np.uint8)
        out = op.compute(img)
        assert out.shape == (10, 10)
        assert out.dtype == np.uint8

    def test_bgra_4channel(self, op):
        img = np.zeros((10, 10, 4), dtype=np.uint8)
        out = op.compute(img)
        assert out.shape == (10, 10)
        assert out.dtype == np.uint8

    def test_single_channel_axis(self, op):
        img = np.zeros((10, 10, 1), dtype=np.uint8)
        out = op.compute(img)
        assert out.shape == (10, 10)
        assert out.dtype == np.uint8


class TestRobertsCrossFloatInput:
    def test_float32_normalised_and_processed(self, op):
        img = np.random.rand(10, 10, 3).astype(np.float32)
        out = op.compute(img)
        assert out.shape == (10, 10)
        assert out.dtype == np.uint8


class TestRobertsCrossEdgeDetection:
    def test_uniform_image_produces_zero_output(self, op):
        img = np.full((10, 10), 128, dtype=np.uint8)
        out = op.compute(img)
        assert out.max() == 0

    def test_edge_detected_on_step_image(self, op):
        img = np.zeros((10, 10), dtype=np.uint8)
        img[:, 5:] = 255
        out = op.compute(img)
        assert out.max() > 0

    def test_does_not_mutate_input(self, op):
        img = np.zeros((10, 10, 3), dtype=np.uint8)
        original = img.copy()
        op.compute(img)
        np.testing.assert_array_equal(img, original)

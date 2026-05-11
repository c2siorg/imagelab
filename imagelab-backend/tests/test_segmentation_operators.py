"""Tests for segmentation operators: KMeansSegmentation and Watershed."""

import numpy as np
import pytest

from app.operators.segmentation.kmeans_segmentation import KMeansSegmentation
from app.operators.segmentation.watershed import Watershed

# Shared fixtures


def make_bgr(h=100, w=100, color=(128, 64, 32)):
    image = np.full((h, w, 3), color, dtype=np.uint8)
    return image


def make_two_region_image():
    """100x100 BGR image with a clear dark/light split — gives watershed distinct regions."""
    image = np.zeros((100, 100, 3), dtype=np.uint8)
    image[:, 50:] = 200
    return image


def make_grayscale(h=100, w=100):
    image = np.zeros((h, w), dtype=np.uint8)
    image[:, 50:] = 200
    return image


def make_bgra(h=100, w=100):
    image = np.zeros((h, w, 4), dtype=np.uint8)
    image[:, 50:] = (200, 200, 200, 255)
    return image


# KMeansSegmentation


class TestKMeansSegmentation:
    def _op(self, params=None):
        return KMeansSegmentation(params or {})

    def test_returns_bgr_image_same_shape(self):
        image = make_bgr()
        result = self._op().compute(image.copy())
        assert result.shape == (100, 100, 3)
        assert result.dtype == np.uint8

    def test_default_params_run_without_error(self):
        result = self._op().compute(make_bgr())
        assert result is not None

    @pytest.mark.parametrize("k", [2, 3, 5, 10])
    def test_valid_k_values(self, k):
        result = self._op({"k": k}).compute(make_bgr())
        assert result.shape == (100, 100, 3)

    def test_k_below_minimum_is_clamped_to_2(self):
        # k=1 is invalid for kmeans; operator clamps to 2 and must not raise
        result = self._op({"k": 1}).compute(make_bgr())
        assert result.shape == (100, 100, 3)

    def test_k_above_maximum_is_clamped_to_10(self):
        result = self._op({"k": 99}).compute(make_bgr())
        assert result.shape == (100, 100, 3)

    def test_grayscale_input_is_converted_and_returns_bgr(self):
        result = self._op().compute(make_grayscale())
        assert result.ndim == 3
        assert result.shape[2] == 3

    def test_bgra_input_is_converted_and_returns_bgr(self):
        result = self._op().compute(make_bgra())
        assert result.ndim == 3
        assert result.shape[2] == 3

    def test_output_pixels_are_cluster_centres(self):
        """Every pixel value in the output must be one of the k centre colours."""
        image = make_two_region_image()
        k = 2
        result = self._op({"k": k}).compute(image.copy())

        pixels = result.reshape(-1, 3)
        unique_colours = np.unique(pixels, axis=0)
        assert len(unique_colours) <= k

    def test_uniform_image_returns_single_colour(self):
        """All pixels identical — result must be a uniform image with one colour."""
        image = np.full((50, 50, 3), 128, dtype=np.uint8)
        result = self._op({"k": 3}).compute(image.copy())
        unique = np.unique(result.reshape(-1, 3), axis=0)
        assert len(unique) == 1

    def test_does_not_mutate_input(self):
        image = make_bgr()
        original = image.copy()
        self._op().compute(image)
        np.testing.assert_array_equal(image, original)

    @pytest.mark.parametrize(
        "params",
        [
            {"k": 3, "max_iter": 10, "epsilon": 1.0, "attempts": 1},
            {"k": 2, "max_iter": 500, "epsilon": 0.01, "attempts": 10},
        ],
    )
    def test_explicit_params_run_without_error(self, params):
        result = self._op(params).compute(make_bgr())
        assert result.shape == (100, 100, 3)

    def test_max_iter_clamped_below_minimum(self):
        result = self._op({"max_iter": 0}).compute(make_bgr())
        assert result.shape == (100, 100, 3)

    def test_attempts_clamped_below_minimum(self):
        result = self._op({"attempts": 0}).compute(make_bgr())
        assert result.shape == (100, 100, 3)


# Watershed


class TestWatershed:
    def _op(self, params=None):
        return Watershed(params or {})

    def test_returns_bgr_image_same_shape(self):
        image = make_two_region_image()
        result = self._op().compute(image.copy())
        assert result.shape == (100, 100, 3)
        assert result.dtype == np.uint8

    def test_default_params_run_without_error(self):
        result = self._op().compute(make_two_region_image())
        assert result is not None

    def test_grayscale_input_is_converted_and_returns_bgr(self):
        result = self._op().compute(make_grayscale())
        assert result.ndim == 3
        assert result.shape[2] == 3

    def test_bgra_input_is_converted_and_returns_bgr(self):
        result = self._op().compute(make_bgra())
        assert result.ndim == 3
        assert result.shape[2] == 3

    def test_boundaries_marked_red(self):
        """Watershed boundaries must be drawn in red (BGR: 0, 0, 255)."""
        image = make_two_region_image()
        result = self._op().compute(image.copy())
        # At least one pixel should be red
        red_mask = (result[:, :, 0] == 0) & (result[:, :, 1] == 0) & (result[:, :, 2] == 255)
        assert red_mask.any(), "expected red boundary pixels in watershed output"

    def test_uniform_image_returns_early_without_error(self):
        """Flat image has dist_max == 0 — operator must return a copy without crashing."""
        image = np.full((100, 100, 3), 255, dtype=np.uint8)
        result = self._op().compute(image.copy())
        assert result.shape == (100, 100, 3)

    @pytest.mark.parametrize("threshold", [0.1, 0.5, 0.9])
    def test_valid_foreground_thresholds(self, threshold):
        result = self._op({"foreground_threshold": threshold}).compute(make_two_region_image())
        assert result.shape == (100, 100, 3)

    def test_foreground_threshold_clamped_below_minimum(self):
        result = self._op({"foreground_threshold": 0.0}).compute(make_two_region_image())
        assert result.shape == (100, 100, 3)

    def test_foreground_threshold_clamped_above_maximum(self):
        result = self._op({"foreground_threshold": 1.0}).compute(make_two_region_image())
        assert result.shape == (100, 100, 3)

    def test_does_not_mutate_input(self):
        image = make_two_region_image()
        original = image.copy()
        self._op().compute(image)
        np.testing.assert_array_equal(image, original)

    def test_output_shape_matches_input_shape(self):
        """Non-square image should produce output with the same spatial dimensions."""
        image = np.zeros((80, 120, 3), dtype=np.uint8)
        image[:, 60:] = 200
        result = self._op().compute(image.copy())
        assert result.shape == (80, 120, 3)

import numpy as np
import pytest

from app.utils.image import compute_image_stats


class TestComputeImageStatsShape:
    def test_grayscale_returns_one_histogram(self):
        img = np.zeros((10, 10), dtype=np.uint8)
        stats = compute_image_stats(img)
        assert stats["channels"] == 1
        assert len(stats["histograms"]) == 1
        assert len(stats["histograms"][0]) == 256

    def test_bgr_returns_three_histograms(self):
        img = np.zeros((10, 10, 3), dtype=np.uint8)
        stats = compute_image_stats(img)
        assert stats["channels"] == 3
        assert len(stats["histograms"]) == 3

    def test_bgra_caps_at_three_histograms(self):
        """Alpha channel must NOT be included in histograms."""
        img = np.zeros((10, 10, 4), dtype=np.uint8)
        stats = compute_image_stats(img)
        assert stats["channels"] == 4
        assert len(stats["histograms"]) == 3  # alpha excluded


class TestComputeImageStatsDimensions:
    def test_width_height_reported_correctly(self):
        img = np.zeros((7, 13, 3), dtype=np.uint8)
        stats = compute_image_stats(img)
        assert stats["height"] == 7
        assert stats["width"] == 13

    def test_dtype_string(self):
        img = np.zeros((5, 5), dtype=np.float32)
        stats = compute_image_stats(img)
        assert stats["dtype"] == "float32"


class TestComputeImageStatsValues:
    def test_uniform_image_min_equals_max(self):
        img = np.full((5, 5), 128, dtype=np.uint8)
        stats = compute_image_stats(img)
        assert stats["min_val"] == 128.0
        assert stats["max_val"] == 128.0

    def test_mean_val_correctness(self):
        img = np.array([[0, 255], [0, 255]], dtype=np.uint8)
        stats = compute_image_stats(img)
        assert stats["mean_val"] == pytest.approx(127.5, abs=0.01)


class TestComputeImageStatsHistogram:
    def test_histogram_sums_to_pixel_count(self):
        img = np.random.randint(0, 256, (20, 20), dtype=np.uint8)
        stats = compute_image_stats(img)
        assert sum(stats["histograms"][0]) == 20 * 20

    def test_float_image_histogram_is_meaningful(self):
        """Regression: float images outside [0,255] must still produce valid histograms."""
        # Values in [0, 1] range (common output from normalised float operators)
        img = np.linspace(0.0, 1.0, 100, dtype=np.float32).reshape(10, 10)
        stats = compute_image_stats(img)
        total = sum(stats["histograms"][0])
        assert total == 100, f"Expected 100 pixels in histogram, got {total}"

    def test_float_image_large_range_histogram_is_meaningful(self):
        """Float values >> 255 must not produce empty histograms."""
        img = np.linspace(0.0, 10000.0, 100, dtype=np.float64).reshape(10, 10)
        stats = compute_image_stats(img)
        total = sum(stats["histograms"][0])
        assert total == 100

    def test_uniform_image_histogram_preserves_true_bucket(self):
        """Uniform uint8 image: pixels must fall in the bucket matching the actual value."""
        img = np.full((10, 10), 42, dtype=np.uint8)
        stats = compute_image_stats(img)
        # Value 42 → bucket 42 (not bucket 0)
        assert stats["histograms"][0][42] == 100
        assert stats["histograms"][0][0] == 0

    def test_uniform_128_histogram_at_bucket_128(self):
        """Regression: all-128 image must report bucket 128, not bucket 0."""
        img = np.full((5, 5), 128, dtype=np.uint8)
        stats = compute_image_stats(img)
        assert stats["histograms"][0][128] == 25
        assert stats["histograms"][0][0] == 0

    def test_uniform_float_05_histogram_maps_to_mid_bucket(self):
        """Uniform float images in [0,1] should map to proportional uint8 buckets."""
        img = np.full((5, 5), 0.5, dtype=np.float32)
        stats = compute_image_stats(img)
        assert stats["histograms"][0][127] == 25
        assert stats["histograms"][0][0] == 0

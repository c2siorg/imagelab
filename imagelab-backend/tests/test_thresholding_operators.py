import numpy as np
import pytest

from app.operators.thresholding.adaptive_threshold import AdaptiveThreshold
from app.operators.thresholding.apply_threshold import ApplyThreshold
from app.operators.thresholding.otsu_threshold import OtsuThreshold


class TestApplyThreshold:
    def test_default_params_output_shape(self, color_image):
        result = ApplyThreshold({}).compute(color_image)
        assert result.shape == color_image.shape

    def test_output_is_uint8(self, color_image):
        result = ApplyThreshold({}).compute(color_image)
        assert result.dtype == np.uint8

    @pytest.mark.xfail(
        strict=True, reason="maxValue defaults to 0 — known bug, fix in fix/apply-threshold-default-max-value"
    )
    def test_default_params_produces_non_empty_output(self, color_image):
        result = ApplyThreshold({}).compute(color_image)
        assert result.max() > 0

    def test_max_value_255_produces_binary_output(self, grayscale_image):
        result = ApplyThreshold({"maxValue": 255, "thresholdValue": 127}).compute(grayscale_image)
        unique = np.unique(result)
        assert set(unique).issubset({0, 255})

    def test_threshold_value_0_pixels_above_zero_become_max(self, grayscale_image):
        result = ApplyThreshold({"maxValue": 255, "thresholdValue": 0}).compute(grayscale_image)
        assert np.all(result[grayscale_image > 0] == 255)
        assert np.all(result[grayscale_image == 0] == 0)

    def test_grayscale_input(self, grayscale_image):
        result = ApplyThreshold({"maxValue": 255, "thresholdValue": 127}).compute(grayscale_image)
        assert result.shape == grayscale_image.shape

    def test_color_input_output_channels(self, color_image):
        result = ApplyThreshold({"maxValue": 255, "thresholdValue": 127}).compute(color_image)
        assert result.shape == color_image.shape

    def test_threshold_at_boundary(self):
        img = np.array([[0, 127, 128, 255]], dtype=np.uint8)
        result = ApplyThreshold({"maxValue": 255, "thresholdValue": 127}).compute(img)
        expected = np.array([[0, 0, 255, 255]], dtype=np.uint8)
        np.testing.assert_array_equal(result, expected)


class TestAdaptiveThreshold:
    def test_default_params_output_shape(self, color_image):
        result = AdaptiveThreshold({}).compute(color_image)
        assert result.shape == color_image.shape[:2]

    def test_output_is_uint8(self, color_image):
        result = AdaptiveThreshold({}).compute(color_image)
        assert result.dtype == np.uint8

    def test_output_is_binary(self, color_image):
        result = AdaptiveThreshold({}).compute(color_image)
        unique = np.unique(result)
        assert set(unique).issubset({0, 255})

    def test_color_input_converts_to_grayscale(self, color_image):
        result = AdaptiveThreshold({}).compute(color_image)
        assert len(result.shape) == 2

    def test_rgba_input(self, color_image):
        rgba = np.dstack([color_image, np.full(color_image.shape[:2], 255, dtype=np.uint8)])
        result = AdaptiveThreshold({}).compute(rgba)
        assert len(result.shape) == 2

    def test_even_block_size_corrected_to_odd(self, color_image):
        result_even = AdaptiveThreshold({"blockSize": 4}).compute(color_image)
        result_odd = AdaptiveThreshold({"blockSize": 5}).compute(color_image)
        np.testing.assert_array_equal(result_even, result_odd)

    def test_gaussian_method(self, color_image):
        result = AdaptiveThreshold({"adaptiveMethod": "GAUSSIAN"}).compute(color_image)
        assert result.shape == color_image.shape[:2]

    def test_mean_method(self, color_image):
        result = AdaptiveThreshold({"adaptiveMethod": "MEAN"}).compute(color_image)
        assert result.shape == color_image.shape[:2]

    def test_grayscale_input(self, grayscale_image):
        result = AdaptiveThreshold({}).compute(grayscale_image)
        assert result.shape == grayscale_image.shape

    def test_invalid_adaptive_method_falls_back_to_gaussian(self, color_image):
        result_invalid = AdaptiveThreshold({"adaptiveMethod": "INVALID"}).compute(color_image)
        result_gaussian = AdaptiveThreshold({"adaptiveMethod": "GAUSSIAN"}).compute(color_image)
        np.testing.assert_array_equal(result_invalid, result_gaussian)


class TestOtsuThreshold:
    def test_default_params_output_shape(self, color_image):
        result = OtsuThreshold({}).compute(color_image)
        assert result.shape == color_image.shape[:2]

    def test_output_is_uint8(self, color_image):
        result = OtsuThreshold({}).compute(color_image)
        assert result.dtype == np.uint8

    def test_output_is_binary(self, color_image):
        result = OtsuThreshold({}).compute(color_image)
        unique = np.unique(result)
        assert set(unique).issubset({0, 255})

    def test_color_input_converts_to_grayscale(self, color_image):
        result = OtsuThreshold({}).compute(color_image)
        assert len(result.shape) == 2

    def test_rgba_input(self, color_image):
        rgba = np.dstack([color_image, np.full(color_image.shape[:2], 255, dtype=np.uint8)])
        result = OtsuThreshold({}).compute(rgba)
        assert len(result.shape) == 2
        assert set(np.unique(result)).issubset({0, 255})

    def test_bgra_input_with_varying_alpha(self, color_image):
        alpha = np.linspace(0, 255, color_image.shape[1], dtype=np.uint8)
        alpha = np.tile(alpha, (color_image.shape[0], 1))
        bgra = np.dstack([color_image, alpha])
        result = OtsuThreshold({}).compute(bgra)
        assert result.shape == color_image.shape[:2]
        assert result.dtype == np.uint8
        assert set(np.unique(result)).issubset({0, 255})

    def test_grayscale_input(self, grayscale_image):
        result = OtsuThreshold({}).compute(grayscale_image)
        assert result.shape == grayscale_image.shape

    def test_custom_max_value(self, grayscale_image):
        result = OtsuThreshold({"maxValue": 128}).compute(grayscale_image)
        unique = np.unique(result)
        assert set(unique).issubset({0, 128})

    def test_otsu_threshold_adapts_to_image_content(self):
        dark_img = np.zeros((100, 100), dtype=np.uint8)
        dark_img[:80, :] = 20
        dark_img[80:, :] = 230
        bright_img = np.zeros((100, 100), dtype=np.uint8)
        bright_img[:20, :] = 20
        bright_img[20:, :] = 230
        result_dark = OtsuThreshold({"maxValue": 255}).compute(dark_img)
        result_bright = OtsuThreshold({"maxValue": 255}).compute(bright_img)
        assert result_dark.mean() != result_bright.mean()

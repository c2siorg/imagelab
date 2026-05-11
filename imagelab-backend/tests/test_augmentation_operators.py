import numpy as np

from app.operators.augmentation.gaussian_noise import GaussianNoise
from app.operators.augmentation.salt_pepper_noise import SaltPepperNoise
from app.operators.augmentation.sepia_filter import SepiaFilter

# GaussianNoise


class TestGaussianNoise:
    def test_default_params_output_shape(self, color_image):
        result = GaussianNoise({}).compute(color_image)
        assert result.shape == color_image.shape

    def test_output_is_uint8(self, color_image):
        result = GaussianNoise({}).compute(color_image)
        assert result.dtype == np.uint8

    def test_grayscale_input(self, grayscale_image):
        result = GaussianNoise({}).compute(grayscale_image)
        assert result.shape == grayscale_image.shape

    def test_rgba_input_preserves_alpha(self, color_image):
        alpha = np.full(color_image.shape[:2], 200, dtype=np.uint8)
        rgba = np.dstack([color_image, alpha])
        result = GaussianNoise({}).compute(rgba)
        assert result.shape == rgba.shape
        np.testing.assert_array_equal(result[:, :, 3], alpha)

    def test_noise_changes_image(self, color_image):
        result = GaussianNoise({"sigma": 25}).compute(color_image)
        assert not np.array_equal(result, color_image)

    def test_fixed_seed_is_deterministic(self, color_image):
        result1 = GaussianNoise({"seed": 42}).compute(color_image)
        result2 = GaussianNoise({"seed": 42}).compute(color_image)
        np.testing.assert_array_equal(result1, result2)

    def test_different_seeds_differ(self, color_image):
        result1 = GaussianNoise({"seed": 1}).compute(color_image)
        result2 = GaussianNoise({"seed": 2}).compute(color_image)
        assert not np.array_equal(result1, result2)

    def test_zero_sigma_clamped_to_minimum(self, color_image):
        result = GaussianNoise({"sigma": 0}).compute(color_image)
        assert result.shape == color_image.shape
        assert result.dtype == np.uint8

    def test_output_values_in_valid_range(self, color_image):
        result = GaussianNoise({"sigma": 100}).compute(color_image)
        assert result.min() >= 0
        assert result.max() <= 255

    def test_invalid_mean_falls_back_to_default(self, color_image):
        result = GaussianNoise({"mean": "bad"}).compute(color_image)
        assert result.shape == color_image.shape

    def test_invalid_sigma_falls_back_to_default(self, color_image):
        result = GaussianNoise({"sigma": "bad"}).compute(color_image)
        assert result.shape == color_image.shape


# SaltPepperNoise


class TestSaltPepperNoise:
    def test_default_params_output_shape(self, color_image):
        result = SaltPepperNoise({}).compute(color_image)
        assert result.shape == color_image.shape

    def test_output_is_uint8(self, color_image):
        result = SaltPepperNoise({}).compute(color_image)
        assert result.dtype == np.uint8

    def test_grayscale_input(self, grayscale_image):
        result = SaltPepperNoise({}).compute(grayscale_image)
        assert result.shape == grayscale_image.shape

    def test_rgba_input_preserves_alpha(self, color_image):
        alpha = np.full(color_image.shape[:2], 200, dtype=np.uint8)
        rgba = np.dstack([color_image, alpha])
        result = SaltPepperNoise({}).compute(rgba)
        assert result.shape == rgba.shape
        np.testing.assert_array_equal(result[:, :, 3], alpha)

    def test_noise_changes_image(self, color_image):
        result = SaltPepperNoise({"density": 0.1}).compute(color_image)
        assert not np.array_equal(result, color_image)

    def test_fixed_seed_is_deterministic(self, color_image):
        result1 = SaltPepperNoise({"seed": 42}).compute(color_image)
        result2 = SaltPepperNoise({"seed": 42}).compute(color_image)
        np.testing.assert_array_equal(result1, result2)

    def test_different_seeds_differ(self, color_image):
        result1 = SaltPepperNoise({"seed": 1}).compute(color_image)
        result2 = SaltPepperNoise({"seed": 2}).compute(color_image)
        assert not np.array_equal(result1, result2)

    def test_zero_density_returns_original(self, color_image):
        result = SaltPepperNoise({"density": 0.0, "seed": 42}).compute(color_image)
        np.testing.assert_array_equal(result, color_image)

    def test_density_clamped_above_1(self, color_image):
        result = SaltPepperNoise({"density": 5.0}).compute(color_image)
        assert result.shape == color_image.shape

    def test_salt_pixels_are_255(self, color_image):
        result = SaltPepperNoise({"density": 0.5, "seed": 42}).compute(color_image)
        assert (result == 255).any()

    def test_pepper_pixels_are_0(self, color_image):
        result = SaltPepperNoise({"density": 0.5, "seed": 42}).compute(color_image)
        assert (result == 0).any()

    def test_invalid_density_falls_back_to_default(self, color_image):
        result = SaltPepperNoise({"density": "bad"}).compute(color_image)
        assert result.shape == color_image.shape


# SepiaFilter


class TestSepiaFilter:
    def test_default_params_output_shape(self, color_image):
        result = SepiaFilter({}).compute(color_image)
        assert result.shape == color_image.shape

    def test_output_is_uint8(self, color_image):
        result = SepiaFilter({}).compute(color_image)
        assert result.dtype == np.uint8

    def test_grayscale_input(self, grayscale_image):
        result = SepiaFilter({}).compute(grayscale_image)
        assert result.shape[:2] == grayscale_image.shape

    def test_rgba_input_preserves_alpha(self, color_image):
        alpha = np.full(color_image.shape[:2], 200, dtype=np.uint8)
        rgba = np.dstack([color_image, alpha])
        result = SepiaFilter({"intensity": 1.0}).compute(rgba)
        assert result.shape == rgba.shape
        np.testing.assert_array_equal(result[:, :, 3], alpha)

    def test_zero_intensity_returns_original(self, color_image):
        result = SepiaFilter({"intensity": 0.0}).compute(color_image)
        np.testing.assert_array_equal(result, color_image)

    def test_full_intensity_produces_warm_tone(self):
        bgr = np.array([[[100, 150, 200]]], dtype=np.uint8)
        result = SepiaFilter({"intensity": 1.0}).compute(bgr)
        assert result[0, 0, 2] > result[0, 0, 1] > result[0, 0, 0]

    def test_intensity_clamped_above_1(self, color_image):
        result = SepiaFilter({"intensity": 5.0}).compute(color_image)
        assert result.shape == color_image.shape

    def test_intensity_clamped_below_0(self, color_image):
        result_clamped = SepiaFilter({"intensity": -1.0}).compute(color_image)
        result_zero = SepiaFilter({"intensity": 0.0}).compute(color_image)
        np.testing.assert_array_equal(result_clamped, result_zero)

    def test_output_values_in_valid_range(self, color_image):
        result = SepiaFilter({"intensity": 1.0}).compute(color_image)
        assert result.min() >= 0
        assert result.max() <= 255

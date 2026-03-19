import numpy as np

from app.operators.blurring.blur import Blur
from app.operators.blurring.gaussian_blur import GaussianBlur
from app.operators.blurring.median_blur import MedianBlur

# Blur


class TestBlur:
    def test_default_params_output_shape(self, color_image):
        result = Blur({}).compute(color_image)
        assert result.shape == color_image.shape

    def test_custom_params_output_shape(self, color_image):
        result = Blur({"widthSize": 5, "heightSize": 5}).compute(color_image)
        assert result.shape == color_image.shape

    def test_grayscale_input(self, grayscale_image):
        result = Blur({}).compute(grayscale_image)
        assert result.shape == grayscale_image.shape

    def test_large_kernel(self, color_image):
        result = Blur({"widthSize": 15, "heightSize": 15}).compute(color_image)
        assert result.shape == color_image.shape

    def test_output_is_uint8(self, color_image):
        result = Blur({}).compute(color_image)
        assert result.dtype == np.uint8

    def test_blur_smooths_image(self):
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        img[::2, ::2] = 255
        result = Blur({"widthSize": 9, "heightSize": 9}).compute(img)
        assert result.std() < img.std()

    def test_kernel_size_1_is_identity(self, color_image):
        result = Blur({"widthSize": 1, "heightSize": 1}).compute(color_image)
        np.testing.assert_array_equal(result, color_image)

    def test_small_image_no_crash(self):
        img = np.zeros((3, 3, 3), dtype=np.uint8)
        result = Blur({"widthSize": 9, "heightSize": 9}).compute(img)
        assert result.shape == img.shape


# GaussianBlur


class TestGaussianBlur:
    def test_default_params_output_shape(self, color_image):
        result = GaussianBlur({}).compute(color_image)
        assert result.shape == color_image.shape

    def test_custom_params_output_shape(self, color_image):
        result = GaussianBlur({"widthSize": 5, "heightSize": 5}).compute(color_image)
        assert result.shape == color_image.shape

    def test_even_kernel_corrected_to_odd(self, color_image):
        result_even = GaussianBlur({"widthSize": 4, "heightSize": 4}).compute(color_image)
        result_odd = GaussianBlur({"widthSize": 5, "heightSize": 5}).compute(color_image)
        assert result_even.shape == color_image.shape
        np.testing.assert_array_equal(result_even, result_odd)

    def test_grayscale_input(self, grayscale_image):
        result = GaussianBlur({}).compute(grayscale_image)
        assert result.shape == grayscale_image.shape

    def test_large_kernel(self, color_image):
        result = GaussianBlur({"widthSize": 15, "heightSize": 15}).compute(color_image)
        assert result.shape == color_image.shape

    def test_output_is_uint8(self, color_image):
        result = GaussianBlur({}).compute(color_image)
        assert result.dtype == np.uint8

    def test_gaussian_blur_smooths_image(self):
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        img[::2, ::2] = 255
        result = GaussianBlur({"widthSize": 9, "heightSize": 9}).compute(img)
        assert result.std() < img.std()

    def test_kernel_size_1_is_identity(self, color_image):
        result = GaussianBlur({"widthSize": 1, "heightSize": 1}).compute(color_image)
        np.testing.assert_array_equal(result, color_image)

    def test_small_image_no_crash(self):
        img = np.zeros((3, 3, 3), dtype=np.uint8)
        result = GaussianBlur({"widthSize": 9, "heightSize": 9}).compute(img)
        assert result.shape == img.shape


# MedianBlur


class TestMedianBlur:
    def test_default_params_output_shape(self, color_image):
        result = MedianBlur({}).compute(color_image)
        assert result.shape == color_image.shape

    def test_custom_params_output_shape(self, color_image):
        result = MedianBlur({"kernelSize": 5}).compute(color_image)
        assert result.shape == color_image.shape

    def test_even_kernel_corrected_to_odd(self, color_image):
        result_even = MedianBlur({"kernelSize": 4}).compute(color_image)
        result_odd = MedianBlur({"kernelSize": 5}).compute(color_image)
        assert result_even.shape == color_image.shape
        np.testing.assert_array_equal(result_even, result_odd)

    def test_grayscale_input(self, grayscale_image):
        result = MedianBlur({}).compute(grayscale_image)
        assert result.shape == grayscale_image.shape

    def test_large_kernel(self, color_image):
        result = MedianBlur({"kernelSize": 11}).compute(color_image)
        assert result.shape == color_image.shape

    def test_output_is_uint8(self, color_image):
        result = MedianBlur({}).compute(color_image)
        assert result.dtype == np.uint8

    def test_median_blur_removes_salt_pepper_noise(self):
        clean = np.full((50, 50, 3), 128, dtype=np.uint8)
        noisy = clean.copy()
        noisy[0::5, 0::5] = 255
        result = MedianBlur({"kernelSize": 3}).compute(noisy)
        assert (
            np.abs(result.astype(int) - clean.astype(int)).mean() < np.abs(noisy.astype(int) - clean.astype(int)).mean()
        )

    def test_kernel_size_1_is_identity(self, color_image):
        result = MedianBlur({"kernelSize": 1}).compute(color_image)
        np.testing.assert_array_equal(result, color_image)

    def test_small_image_no_crash(self):
        img = np.zeros((3, 3, 3), dtype=np.uint8)
        result = MedianBlur({"kernelSize": 9}).compute(img)
        assert result.shape == img.shape

import numpy as np
import pytest

from app.operators.conversions.bgr_to_hsv import BgrToHsv
from app.operators.conversions.bgr_to_lab import BgrToLab
from app.operators.conversions.bgr_to_ycrcb import BgrToYcrcb
from app.operators.conversions.brightness_contrast import BrightnessContrast
from app.operators.conversions.channel_split import ChannelSplit
from app.operators.conversions.color_maps import ColorMaps
from app.operators.conversions.color_to_binary import ColorToBinary
from app.operators.conversions.gray_image import GrayImage
from app.operators.conversions.gray_to_binary import GrayToBinary
from app.operators.conversions.histogram_equalization import HistogramEqualization
from app.operators.conversions.hsv_to_bgr import HsvToBgr
from app.operators.conversions.lab_to_bgr import LabToBgr
from app.operators.conversions.ycrcb_to_bgr import YcrcbToBgr


# Fixed-seed fixtures for deterministic tests
@pytest.fixture
def color_image():
    rng = np.random.default_rng(42)
    return rng.integers(0, 256, (100, 100, 3), dtype=np.uint8)


@pytest.fixture
def grayscale_image():
    rng = np.random.default_rng(42)
    return rng.integers(0, 256, (100, 100), dtype=np.uint8)


@pytest.fixture
def rgba_image():
    rng = np.random.default_rng(42)
    return rng.integers(0, 256, (100, 100, 4), dtype=np.uint8)


# GrayImage


class TestGrayImage:
    def test_output_is_grayscale(self, color_image):
        result = GrayImage({}).compute(color_image)
        assert len(result.shape) == 2

    def test_output_shape(self, color_image):
        result = GrayImage({}).compute(color_image)
        assert result.shape == (100, 100)

    def test_output_is_uint8(self, color_image):
        result = GrayImage({}).compute(color_image)
        assert result.dtype == np.uint8


# GrayToBinary


class TestGrayToBinary:
    def test_default_params_output_shape(self, grayscale_image):
        result = GrayToBinary({}).compute(grayscale_image)
        assert result.shape == grayscale_image.shape

    def test_custom_threshold_output_shape(self, grayscale_image):
        result = GrayToBinary({"thresholdValue": 127, "maxValue": 255}).compute(grayscale_image)
        assert result.shape == grayscale_image.shape

    def test_output_is_binary_values(self):
        # Synthetic image that guarantees pixels on both sides of threshold
        img = np.zeros((100, 100), dtype=np.uint8)
        img[:50, :] = 50  # below threshold -> 0
        img[50:, :] = 200  # above threshold -> 255
        result = GrayToBinary({"thresholdValue": 100, "maxValue": 255}).compute(img)
        assert set(np.unique(result)) == {0, 255}

    def test_output_is_uint8(self, grayscale_image):
        result = GrayToBinary({"thresholdValue": 127, "maxValue": 255}).compute(grayscale_image)
        assert result.dtype == np.uint8


# ColorToBinary


class TestColorToBinary:
    def test_default_params_output_shape(self, color_image):
        result = ColorToBinary({}).compute(color_image)
        assert result.shape == (100, 100)

    def test_output_is_grayscale(self, color_image):
        result = ColorToBinary({}).compute(color_image)
        assert len(result.shape) == 2

    def test_output_is_binary_values(self):
        # Synthetic image that guarantees pixels on both sides of threshold
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        img[:50, :] = 50  # below threshold -> 0
        img[50:, :] = 200  # above threshold -> 255
        result = ColorToBinary({"thresholdValue": 100, "maxValue": 255}).compute(img)
        assert set(np.unique(result)) == {0, 255}

    def test_threshold_binary_inv(self, color_image):
        result = ColorToBinary(
            {"thresholdType": "threshold_binary_inv", "thresholdValue": 127, "maxValue": 255}
        ).compute(color_image)
        assert result.shape == (100, 100)

    def test_output_is_uint8(self, color_image):
        result = ColorToBinary({"thresholdValue": 127, "maxValue": 255}).compute(color_image)
        assert result.dtype == np.uint8


# ColorMaps


class TestColorMaps:
    @pytest.mark.parametrize(
        "colormap", ["HOT", "AUTUMN", "BONE", "COOL", "HSV", "JET", "OCEAN", "PARULA", "PINK", "RAINBOW"]
    )
    def test_all_colormaps_output_shape(self, grayscale_image, colormap):
        result = ColorMaps({"type": colormap}).compute(grayscale_image)
        assert result.shape[:2] == grayscale_image.shape[:2]

    def test_default_colormap_output_shape(self, grayscale_image):
        result = ColorMaps({}).compute(grayscale_image)
        assert result.shape[:2] == grayscale_image.shape[:2]

    def test_output_is_bgr(self, grayscale_image):
        result = ColorMaps({}).compute(grayscale_image)
        assert result.shape[2] == 3

    def test_output_is_uint8(self, grayscale_image):
        result = ColorMaps({}).compute(grayscale_image)
        assert result.dtype == np.uint8


# ChannelSplit


class TestChannelSplit:
    @pytest.mark.parametrize("channel", ["RED", "GREEN", "BLUE"])
    def test_all_channels_output_shape(self, color_image, channel):
        result = ChannelSplit({"channel": channel}).compute(color_image)
        assert result.shape == (100, 100)

    def test_default_channel_is_red(self, color_image):
        default_result = ChannelSplit({}).compute(color_image)
        explicit_red = ChannelSplit({"channel": "RED"}).compute(color_image)
        np.testing.assert_array_equal(default_result, explicit_red)

    def test_output_is_uint8(self, color_image):
        result = ChannelSplit({}).compute(color_image)
        assert result.dtype == np.uint8

    def test_grayscale_input_returned_as_is(self, grayscale_image):
        result = ChannelSplit({}).compute(grayscale_image)
        np.testing.assert_array_equal(result, grayscale_image)

    def test_rgba_input_splits_correctly(self, rgba_image):
        result = ChannelSplit({"channel": "BLUE"}).compute(rgba_image)
        assert result.shape == (100, 100)
        # In OpenCV BGRA layout, channel index 0 is Blue
        expected = rgba_image[:, :, 0]
        np.testing.assert_array_equal(result, expected)


# BgrToHsv


class TestBgrToHsv:
    def test_output_shape(self, color_image):
        result = BgrToHsv({}).compute(color_image)
        assert result.shape == color_image.shape

    def test_grayscale_input_produces_hsv_output(self, grayscale_image):
        result = BgrToHsv({}).compute(grayscale_image)
        assert result.shape[2] == 3

    def test_rgba_input_produces_hsv_output(self, rgba_image):
        result = BgrToHsv({}).compute(rgba_image)
        assert result.shape[2] == 3

    def test_output_is_uint8(self, color_image):
        result = BgrToHsv({}).compute(color_image)
        assert result.dtype == np.uint8

    def test_hsv_channel_ranges(self, color_image):
        result = BgrToHsv({}).compute(color_image)
        H, S, V = result[:, :, 0], result[:, :, 1], result[:, :, 2]
        assert H.min() >= 0 and H.max() <= 179
        assert S.min() >= 0 and S.max() <= 255
        assert V.min() >= 0 and V.max() <= 255


# HsvToBgr


class TestHsvToBgr:
    def test_roundtrip_output_shape(self, color_image):
        hsv = BgrToHsv({}).compute(color_image)
        result = HsvToBgr({}).compute(hsv)
        assert result.shape == color_image.shape

    def test_roundtrip_preserves_values(self, color_image):
        hsv = BgrToHsv({}).compute(color_image)
        result = HsvToBgr({}).compute(hsv)
        np.testing.assert_allclose(
            result.astype(np.int32),
            color_image.astype(np.int32),
            atol=5,
            err_msg="BGR→HSV→BGR round-trip should preserve pixel values",
        )

    def test_valid_hsv_input_returns_bgr(self, color_image):
        hsv = BgrToHsv({}).compute(color_image)
        result = HsvToBgr({}).compute(hsv)
        assert result.shape[2] == 3
        assert result.dtype == np.uint8

    def test_output_is_uint8(self, color_image):
        hsv = BgrToHsv({}).compute(color_image)
        result = HsvToBgr({}).compute(hsv)
        assert result.dtype == np.uint8


# BgrToLab


class TestBgrToLab:
    def test_output_shape(self, color_image):
        result = BgrToLab({}).compute(color_image)
        assert result.shape == color_image.shape

    def test_grayscale_input_produces_lab_output(self, grayscale_image):
        result = BgrToLab({}).compute(grayscale_image)
        assert result.shape[2] == 3

    def test_rgba_input_produces_lab_output(self, rgba_image):
        result = BgrToLab({}).compute(rgba_image)
        assert result.shape[2] == 3

    def test_output_is_uint8(self, color_image):
        result = BgrToLab({}).compute(color_image)
        assert result.dtype == np.uint8


# LabToBgr


class TestLabToBgr:
    def test_roundtrip_output_shape(self, color_image):
        lab = BgrToLab({}).compute(color_image)
        result = LabToBgr({}).compute(lab)
        assert result.shape == color_image.shape

    def test_roundtrip_preserves_values(self, color_image):
        lab = BgrToLab({}).compute(color_image)
        result = LabToBgr({}).compute(lab)
        np.testing.assert_allclose(
            result.astype(np.int32),
            color_image.astype(np.int32),
            atol=25,
            err_msg="BGR→Lab→BGR round-trip should preserve pixel values",
        )

    def test_valid_lab_input_returns_bgr(self, color_image):
        lab = BgrToLab({}).compute(color_image)
        result = LabToBgr({}).compute(lab)
        assert result.shape[2] == 3
        assert result.dtype == np.uint8

    def test_output_is_uint8(self, color_image):
        lab = BgrToLab({}).compute(color_image)
        result = LabToBgr({}).compute(lab)
        assert result.dtype == np.uint8


# BgrToYcrcb


class TestBgrToYcrcb:
    def test_output_shape(self, color_image):
        result = BgrToYcrcb({}).compute(color_image)
        assert result.shape == color_image.shape

    def test_grayscale_input_produces_ycrcb_output(self, grayscale_image):
        result = BgrToYcrcb({}).compute(grayscale_image)
        assert result.shape[2] == 3

    def test_rgba_input_produces_ycrcb_output(self, rgba_image):
        result = BgrToYcrcb({}).compute(rgba_image)
        assert result.shape[2] == 3

    def test_output_is_uint8(self, color_image):
        result = BgrToYcrcb({}).compute(color_image)
        assert result.dtype == np.uint8


# YcrcbToBgr


class TestYcrcbToBgr:
    def test_roundtrip_output_shape(self, color_image):
        ycrcb = BgrToYcrcb({}).compute(color_image)
        result = YcrcbToBgr({}).compute(ycrcb)
        assert result.shape == color_image.shape

    def test_roundtrip_preserves_values(self, color_image):
        ycrcb = BgrToYcrcb({}).compute(color_image)
        result = YcrcbToBgr({}).compute(ycrcb)
        np.testing.assert_allclose(
            result.astype(np.int32),
            color_image.astype(np.int32),
            atol=2,
            err_msg="BGR→YCrCb→BGR round-trip should preserve pixel values",
        )

    def test_valid_ycrcb_input_returns_bgr(self, color_image):
        ycrcb = BgrToYcrcb({}).compute(color_image)
        result = YcrcbToBgr({}).compute(ycrcb)
        assert result.shape[2] == 3
        assert result.dtype == np.uint8

    def test_output_is_uint8(self, color_image):
        ycrcb = BgrToYcrcb({}).compute(color_image)
        result = YcrcbToBgr({}).compute(ycrcb)
        assert result.dtype == np.uint8


# Error conditions / fallback behaviour


class TestColorMapsFallback:
    def test_unknown_colormap_falls_back_to_hot(self, grayscale_image):
        result_unknown = ColorMaps({"type": "INVALID_MAP"}).compute(grayscale_image)
        result_hot = ColorMaps({"type": "HOT"}).compute(grayscale_image)
        np.testing.assert_array_equal(result_unknown, result_hot)


class TestChannelSplitFallback:
    def test_unknown_channel_falls_back_to_red(self, color_image):
        result_unknown = ChannelSplit({"channel": "INVALID_CHANNEL"}).compute(color_image)
        result_red = ChannelSplit({"channel": "RED"}).compute(color_image)
        np.testing.assert_array_equal(result_unknown, result_red)


class TestColorToBinaryFallback:
    def test_unknown_threshold_type_falls_back_to_binary(self, color_image):
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        img[:50, :] = 50
        img[50:, :] = 200
        result_unknown = ColorToBinary(
            {"thresholdType": "invalid_type", "thresholdValue": 100, "maxValue": 255}
        ).compute(img)
        result_default = ColorToBinary(
            {"thresholdType": "threshold_binary", "thresholdValue": 100, "maxValue": 255}
        ).compute(img)
        np.testing.assert_array_equal(result_unknown, result_default)


# BrightnessContrast


class TestBrightnessContrast:
    def test_default_params_no_change(self, color_image):
        result = BrightnessContrast({}).compute(color_image)
        np.testing.assert_array_equal(result, color_image)

    def test_brightness_increase(self, color_image):
        result = BrightnessContrast({"brightness": 50}).compute(color_image)
        assert result.shape == color_image.shape
        assert result.dtype == np.uint8
        # Pixels should be brighter (higher values)
        assert np.mean(result) > np.mean(color_image)

    def test_contrast_increase(self, color_image):
        result = BrightnessContrast({"contrast": 1.5}).compute(color_image)
        assert result.shape == color_image.shape
        assert result.dtype == np.uint8

    def test_grayscale_input(self, grayscale_image):
        result = BrightnessContrast({"brightness": 30, "contrast": 1.2}).compute(grayscale_image)
        assert result.shape == grayscale_image.shape
        assert result.dtype == np.uint8

    def test_output_clipped_to_uint8_range(self, color_image):
        result = BrightnessContrast({"brightness": 500, "contrast": 5.0}).compute(color_image)
        assert np.all(result >= 0)
        assert np.all(result <= 255)


# HistogramEqualization


class TestHistogramEqualization:
    def test_grayscale_input(self, grayscale_image):
        result = HistogramEqualization({}).compute(grayscale_image)
        assert result.shape == grayscale_image.shape
        assert result.dtype == np.uint8

    def test_color_image_input(self, color_image):
        result = HistogramEqualization({}).compute(color_image)
        assert result.shape == color_image.shape
        assert result.dtype == np.uint8

    def test_rgba_image_input(self, rgba_image):
        result = HistogramEqualization({}).compute(rgba_image)
        assert result.shape == rgba_image.shape
        assert result.shape[2] == 4
        assert result.dtype == np.uint8

    def test_improves_contrast(self):
        # Create a low-contrast image with narrow range
        low_contrast = np.concatenate(
            [np.full((50, 100), 120, dtype=np.uint8), np.full((50, 100), 135, dtype=np.uint8)]
        )
        result = HistogramEqualization({}).compute(low_contrast)
        # Equalized image should have wider range of values
        assert np.max(result) > np.max(low_contrast)
        assert np.std(result) > np.std(low_contrast)

    def test_output_is_uint8(self, color_image):
        result = HistogramEqualization({}).compute(color_image)
        assert result.dtype == np.uint8

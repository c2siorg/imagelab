import numpy as np
import pytest

from app.operators.conversions.brightness_contrast import BrightnessContrast


class TestBrightnessContrast:
    @pytest.fixture
    def image_bgr(self):
        return np.full((100, 100, 3), 128, dtype=np.uint8)

    def test_default_params_no_change(self, image_bgr):
        operator = BrightnessContrast({})
        result = operator.compute(image_bgr.copy())
        assert np.array_equal(result, image_bgr)

    def test_brightness_increase(self, image_bgr):
        operator = BrightnessContrast({"brightness": 50})
        result = operator.compute(image_bgr.copy())
        # All pixels should be 128 + 50 = 178
        assert np.all(result == 178)

    def test_contrast_increase(self, image_bgr):
        # Create non-uniform image
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        img[40:60, 40:60, :] = 100
        operator = BrightnessContrast({"contrast": 2.0})
        result = operator.compute(img.copy())
        # 100 * 2.0 = 200
        assert np.all(result[40:60, 40:60, :] == 200)
        assert np.all(result[0:10, 0:10, :] == 0)

    def test_invalid_brightness_raises(self):
        operator = BrightnessContrast({"brightness": 200})
        with pytest.raises(ValueError, match="Brightness must be between"):
            operator.compute(np.zeros((100, 100), dtype=np.uint8))

    def test_invalid_contrast_raises(self):
        operator = BrightnessContrast({"contrast": 5.0})
        with pytest.raises(ValueError, match="Contrast must be between"):
            operator.compute(np.zeros((100, 100), dtype=np.uint8))

    def test_bgra_alpha_preserved(self, image_bgr):
        alpha = np.full((100, 100), 128, dtype=np.uint8)
        image_bgra = np.dstack([image_bgr, alpha])
        operator = BrightnessContrast({"brightness": 50})
        result = operator.compute(image_bgra.copy())
        assert result.shape == (100, 100, 4)
        assert np.all(result[:, :, 3] == 128)
        assert np.all(result[:, :, :3] == 178)

    def test_output_is_uint8(self, image_bgr):
        operator = BrightnessContrast({"contrast": 1.5, "brightness": 10})
        result = operator.compute(image_bgr)
        assert result.dtype == np.uint8

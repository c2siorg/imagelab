import numpy as np
import pytest

from app.operators.conversions.histogram_equalization import HistogramEqualization


class TestHistogramEqualization:
    @pytest.fixture
    def image_bgr(self):
        # Create an image with low contrast to see the effect
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        img[25:75, 25:75, :] = 100
        return img

    def test_grayscale_input(self):
        image_gray = np.zeros((100, 100), dtype=np.uint8)
        image_gray[25:75, 25:75] = 100
        operator = HistogramEqualization({})
        result = operator.compute(image_gray.copy())
        assert result.shape == (100, 100)
        assert result.dtype == np.uint8
        # Contrast should increase (mean should change or standard deviation should increase)
        assert not np.array_equal(result, image_gray)

    def test_bgr_input_shape_preserved(self, image_bgr):
        operator = HistogramEqualization({})
        result = operator.compute(image_bgr.copy())
        assert result.shape == (100, 100, 3)
        assert result.dtype == np.uint8

    def test_bgra_alpha_preserved(self, image_bgr):
        alpha = np.full((100, 100), 128, dtype=np.uint8)
        image_bgra = np.dstack([image_bgr, alpha])
        operator = HistogramEqualization({})
        result = operator.compute(image_bgra.copy())
        assert result.shape == (100, 100, 4)
        assert np.all(result[:, :, 3] == 128)
        assert not np.array_equal(result[:, :, :3], image_bgr)

    def test_output_is_uint8(self, image_bgr):
        operator = HistogramEqualization({})
        result = operator.compute(image_bgr)
        assert result.dtype == np.uint8

    def test_equalization_increases_contrast(self):
        # Using a very low contrast image
        image_gray = np.full((100, 100), 120, dtype=np.uint8)
        image_gray[40:60, 40:60] = 130
        operator = HistogramEqualization({})
        result = operator.compute(image_gray.copy())
        
        # Original contrast (range) is 10
        # Equalized contrast should be much higher (usually near 255 if enough pixels)
        assert np.ptp(result) > np.ptp(image_gray)

    def test_invalid_dtype_raises(self):
        image_float = np.zeros((100, 100), dtype=np.float32)
        operator = HistogramEqualization({})
        with pytest.raises(ValueError, match="uint8"):
            operator.compute(image_float)

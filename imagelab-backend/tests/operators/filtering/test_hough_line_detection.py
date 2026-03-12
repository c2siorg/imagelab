import cv2
import numpy as np
import pytest

from app.operators.filtering.hough_line_detection import HoughLineDetection


class TestHoughLineDetection:
    @pytest.fixture
    def image_with_line(self):
        # Create a black image with a white line
        img = np.zeros((200, 200, 3), dtype=np.uint8)
        cv2.line(img, (50, 50), (150, 150), (255, 255, 255), 2)
        return img

    def test_default_params_returns_image(self, image_with_line):
        operator = HoughLineDetection({})
        result = operator.compute(image_with_line.copy())
        assert result.shape == (200, 200, 3)
        assert result.dtype == np.uint8

    def test_output_shape_preserved(self, image_with_line):
        operator = HoughLineDetection({})
        result = operator.compute(image_with_line)
        assert result.shape == image_with_line.shape

    def test_output_is_uint8(self, image_with_line):
        operator = HoughLineDetection({})
        result = operator.compute(image_with_line)
        assert result.dtype == np.uint8

    def test_bgra_input_returns_bgr(self):
        img_bgra = np.zeros((100, 100, 4), dtype=np.uint8)
        operator = HoughLineDetection({})
        result = operator.compute(img_bgra)
        assert result.shape == (100, 100, 3)

    def test_no_lines_returns_original_shape(self):
        # Empty black image
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        operator = HoughLineDetection({"threshold": 250}) # High threshold, no lines
        result = operator.compute(img)
        assert result.shape == (100, 100, 3)
        assert np.all(result == 0)

    def test_invalid_thickness_raises(self):
        operator = HoughLineDetection({"thickness": 0})
        with pytest.raises(ValueError, match="thickness must be > 0"):
            operator.compute(np.zeros((100, 100, 3), dtype=np.uint8))

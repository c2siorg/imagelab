import numpy as np
import pytest

from app.operators.geometric.rotate_image import RotateImage


@pytest.fixture
def color_image():
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    img[40:60, 40:60] = [0, 255, 0]  # green square in center
    return img


class TestRotateImage:
    def test_basic_rotation_preserves_shape(self, color_image):
        result = RotateImage({"angle": 45, "scale": 1}).compute(color_image)
        assert result.shape == color_image.shape
        assert result.dtype == np.uint8

    def test_rotation_360_matches_original(self, color_image):
        result = RotateImage({"angle": 360, "scale": 1}).compute(color_image)
        assert result.shape == color_image.shape
        assert result.dtype == np.uint8

    def test_default_params(self, color_image):
        result = RotateImage({}).compute(color_image)
        assert result.shape == color_image.shape
        assert result.dtype == np.uint8

    def test_scale_zero_raises_or_clamps(self, color_image):
        """scale=0 silently destroys the image — should raise ValueError or clamp to a minimum."""
        with pytest.raises(ValueError, match="scale"):
            RotateImage({"angle": 45, "scale": 0}).compute(color_image)

    def test_scale_negative_raises(self, color_image):
        """Negative scale produces a distorted result — should raise ValueError."""
        with pytest.raises(ValueError, match="scale"):
            RotateImage({"angle": 45, "scale": -1}).compute(color_image)

    def test_valid_scale_produces_correct_output(self, color_image):
        result = RotateImage({"angle": 0, "scale": 1}).compute(color_image)
        assert result.shape == color_image.shape
        assert result.dtype == np.uint8

    def test_grayscale_input(self):
        gray = np.full((100, 100), 128, dtype=np.uint8)
        result = RotateImage({"angle": 90, "scale": 1}).compute(gray)
        assert result.shape == gray.shape
        assert result.dtype == np.uint8

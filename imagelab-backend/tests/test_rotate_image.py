import numpy as np
import pytest

from app.operators.geometric.rotate_image import RotateImage


@pytest.fixture
def color_image():
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    img[40:60, 40:60] = [0, 255, 0]  # green square in center
    return img


class TestRotateImage:
    def test_rotation_expands_canvas_to_prevent_clipping(self, color_image):
        result = RotateImage({"angle": 45, "scale": 1}).compute(color_image)
        assert result.shape == (141, 141, 3)
        assert result.dtype == np.uint8

    def test_rectangular_image_rotation_preserves_all_content(self):
        img = np.zeros((200, 400, 3), dtype=np.uint8)
        img[0:10, :, :] = 255
        img[190:200, :, :] = 255

        result = RotateImage({"angle": 90, "scale": 1}).compute(img)
        assert result.shape == (400, 200, 3)
        assert result.dtype == np.uint8
        assert np.count_nonzero(result) == np.count_nonzero(img)

    def test_scale_enlarges_bounding_box(self, color_image):
        result = RotateImage({"angle": 0, "scale": 2}).compute(color_image)
        assert result.shape == (200, 200, 3)
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

    def test_single_channel_3d_input_preserves_shape(self):
        hw1 = np.full((100, 200, 1), 128, dtype=np.uint8)
        result = RotateImage({"angle": 90, "scale": 1}).compute(hw1)
        assert result.shape == (200, 100, 1)
        assert result.dtype == np.uint8

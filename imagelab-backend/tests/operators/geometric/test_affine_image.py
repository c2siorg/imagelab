import cv2
import numpy as np
import pytest

from app.operators.geometric.affine_image import AffineImage


class TestAffineImage:
    @pytest.fixture
    def image(self):
        # Create a simple image with a white dot at (10, 10)
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        img[10, 10] = 255
        return img

    def test_identity_transform(self, image):
        operator = AffineImage({})
        result = operator.compute(image.copy())
        assert result.shape == (100, 100, 3)
        assert np.array_equal(result, image)

    def test_translation(self, image):
        operator = AffineImage({
            "translate_x": 10,
            "translate_y": 20
        })
        result = operator.compute(image.copy())
        # The dot at (10, 10) should move to (20, 30) -> [30, 20] in numpy
        assert np.array_equal(result[30, 20], [255, 255, 255])
        assert result[10, 10][0] == 0

    def test_scaling(self, image):
        operator = AffineImage({
            "scale_x": 2.0,
            "scale_y": 0.5
        })
        result = operator.compute(image.copy())
        # Dot at (10, 10) -> (20, 5) -> [5, 20] in numpy
        assert np.array_equal(result[5, 20], [255, 255, 255])

    def test_shearing(self, image):
        operator = AffineImage({
            "shear_x": 0.5
        })
        result = operator.compute(image.copy())
        # (x, y) -> (x + 0.5y, y)
        # Dot at (10, 10) -> (10 + 0.5*10, 10) = (15, 10) -> [10, 15] in numpy
        assert np.array_equal(result[10, 15], [255, 255, 255])

"""Tests for geometric operators."""

import numpy as np

from app.operators.geometric.affine_image import AffineImage
from app.operators.geometric.crop_image import CropImage
from app.operators.geometric.reflect_image import ReflectImage
from app.operators.geometric.rotate_image import RotateImage
from app.operators.geometric.scale_image import ScaleImage


class TestCropImage:
    """Test cases for CropImage operator."""

    def test_crop_basic(self):
        """Test basic cropping."""
        image = np.ones((100, 100, 3), dtype=np.uint8) * 128
        operator = CropImage({"x1": 10, "y1": 10, "x2": 60, "y2": 60})
        result = operator.compute(image)
        assert result.shape == (50, 50, 3)

    def test_crop_full_image(self):
        """Test cropping the entire image."""
        image = np.ones((100, 100, 3), dtype=np.uint8) * 128
        operator = CropImage({"x1": 0, "y1": 0, "x2": 100, "y2": 100})
        result = operator.compute(image)
        assert result.shape == (100, 100, 3)
        assert np.array_equal(result, image)

    def test_crop_small_region(self):
        """Test cropping a small region."""
        image = np.ones((100, 100, 3), dtype=np.uint8) * 128
        operator = CropImage({"x1": 25, "y1": 25, "x2": 35, "y2": 35})
        result = operator.compute(image)
        assert result.shape == (10, 10, 3)

    def test_crop_grayscale(self):
        """Test cropping grayscale image."""
        image = np.ones((100, 100), dtype=np.uint8) * 128
        operator = CropImage({"x1": 10, "y1": 10, "x2": 60, "y2": 60})
        result = operator.compute(image)
        assert result.shape == (50, 50)

    def test_crop_corner(self):
        """Test cropping from corner."""
        image = np.ones((100, 100, 3), dtype=np.uint8) * 128
        operator = CropImage({"x1": 0, "y1": 0, "x2": 50, "y2": 50})
        result = operator.compute(image)
        assert result.shape == (50, 50, 3)


class TestRotateImage:
    """Test cases for RotateImage operator."""

    def test_rotate_90_degrees(self):
        """Test 90 degree rotation — output canvas keeps original dimensions."""
        image = np.ones((100, 50, 3), dtype=np.uint8) * 128
        result = RotateImage({"angle": 90}).compute(image)
        assert result.shape[0] == 100 and result.shape[1] == 50

    def test_rotate_180_degrees(self):
        """Test 180 degree rotation."""
        image = np.ones((100, 100, 3), dtype=np.uint8) * 128
        operator = RotateImage({"angle": 180})
        result = operator.compute(image)
        assert result.shape == image.shape

    def test_rotate_negative_angle(self):
        """Test negative angle rotation."""
        image = np.ones((100, 100, 3), dtype=np.uint8) * 128
        operator = RotateImage({"angle": -45})
        result = operator.compute(image)
        assert result.shape[0] > 0 and result.shape[1] > 0

    def test_rotate_zero_degrees(self):
        """Test zero degree rotation (no change)."""
        image = np.ones((100, 100, 3), dtype=np.uint8) * 128
        operator = RotateImage({"angle": 0})
        result = operator.compute(image)
        assert result.shape == image.shape

    def test_rotate_45_degrees(self):
        """Test 45 degree rotation."""
        image = np.ones((100, 100, 3), dtype=np.uint8) * 128
        operator = RotateImage({"angle": 45})
        result = operator.compute(image)
        assert result.shape[0] > 0 and result.shape[1] > 0


class TestScaleImage:
    """Test cases for ScaleImage operator."""

    def test_scale_up(self):
        """Test scaling up."""
        image = np.ones((100, 100, 3), dtype=np.uint8) * 128
        operator = ScaleImage({"fx": 2.0, "fy": 2.0})
        result = operator.compute(image)
        assert result.shape[0] == 200 and result.shape[1] == 200

    def test_scale_down(self):
        """Test scaling down."""
        image = np.ones((100, 100, 3), dtype=np.uint8) * 128
        operator = ScaleImage({"fx": 0.5, "fy": 0.5})
        result = operator.compute(image)
        assert result.shape[0] == 50 and result.shape[1] == 50

    def test_scale_one(self):
        """Test scale factor of 1 (no change)."""
        image = np.ones((100, 100, 3), dtype=np.uint8) * 128
        operator = ScaleImage({"fx": 1.0, "fy": 1.0})
        result = operator.compute(image)
        assert result.shape == image.shape

    def test_scale_1_5x(self):
        """Test 1.5x scaling."""
        image = np.ones((100, 100, 3), dtype=np.uint8) * 128
        operator = ScaleImage({"fx": 1.5, "fy": 1.5})
        result = operator.compute(image)
        assert result.shape[0] == 150 and result.shape[1] == 150

    def test_scale_grayscale(self):
        """Test scaling grayscale image."""
        image = np.ones((100, 100), dtype=np.uint8) * 128
        operator = ScaleImage({"fx": 2.0, "fy": 2.0})
        result = operator.compute(image)
        assert result.shape == (200, 200)


class TestReflectImage:
    """Test cases for ReflectImage operator."""

    def test_reflect_horizontal(self):
        """Test horizontal (left-right) reflection using type='Y'."""
        image = np.zeros((100, 100, 3), dtype=np.uint8)
        image[:, :50] = 100
        image[:, 50:] = 200
        operator = ReflectImage({"type": "Y"})
        result = operator.compute(image)
        assert result.shape == image.shape
        assert np.all(result[:, :50] == 200)
        assert np.all(result[:, 50:] == 100)

    def test_reflect_vertical(self):
        """Test vertical (top-bottom) reflection using type='X'."""
        image = np.zeros((100, 100, 3), dtype=np.uint8)
        image[:50, :] = 100
        image[50:, :] = 200
        operator = ReflectImage({"type": "X"})
        result = operator.compute(image)
        assert result.shape == image.shape
        assert np.all(result[:50, :] == 200)
        assert np.all(result[50:, :] == 100)

    def test_reflect_both(self):
        """Test reflection both ways."""
        image = np.ones((100, 100, 3), dtype=np.uint8) * 128
        operator = ReflectImage({"type": "Both"})
        result = operator.compute(image)
        assert result.shape == image.shape

    def test_reflect_grayscale_horizontal(self):
        """Test horizontal reflection on grayscale."""
        image = np.zeros((100, 100), dtype=np.uint8)
        image[:, :50] = 100
        image[:, 50:] = 200
        operator = ReflectImage({"type": "Y"})
        result = operator.compute(image)
        assert result.shape == image.shape


class TestAffineImage:
    """Test cases for AffineImage operator."""

    def test_affine_basic(self):
        """Test basic affine transformation."""
        image = np.ones((100, 100, 3), dtype=np.uint8) * 128
        operator = AffineImage(
            {
                "src_pt1_x": 0,
                "src_pt1_y": 0,
                "src_pt2_x": 100,
                "src_pt2_y": 0,
                "src_pt3_x": 0,
                "src_pt3_y": 100,
                "dst_pt1_x": 0,
                "dst_pt1_y": 0,
                "dst_pt2_x": 100,
                "dst_pt2_y": 0,
                "dst_pt3_x": 0,
                "dst_pt3_y": 100,
            }
        )
        result = operator.compute(image)
        assert result.shape[0] > 0 and result.shape[1] > 0

    def test_affine_skew(self):
        """Test affine skew transformation."""
        image = np.ones((100, 100, 3), dtype=np.uint8) * 128
        operator = AffineImage(
            {
                "src_pt1_x": 0,
                "src_pt1_y": 0,
                "src_pt2_x": 100,
                "src_pt2_y": 0,
                "src_pt3_x": 0,
                "src_pt3_y": 100,
                "dst_pt1_x": 10,
                "dst_pt1_y": 0,
                "dst_pt2_x": 100,
                "dst_pt2_y": 0,
                "dst_pt3_x": 0,
                "dst_pt3_y": 100,
            }
        )
        result = operator.compute(image)
        assert result.shape[0] > 0 and result.shape[1] > 0

    def test_affine_scale(self):
        """Test affine scaling transformation."""
        image = np.ones((100, 100, 3), dtype=np.uint8) * 128
        operator = AffineImage(
            {
                "src_pt1_x": 0,
                "src_pt1_y": 0,
                "src_pt2_x": 100,
                "src_pt2_y": 0,
                "src_pt3_x": 0,
                "src_pt3_y": 100,
                "dst_pt1_x": 0,
                "dst_pt1_y": 0,
                "dst_pt2_x": 200,
                "dst_pt2_y": 0,
                "dst_pt3_x": 0,
                "dst_pt3_y": 200,
            }
        )
        result = operator.compute(image)
        assert result.shape[0] > 0 and result.shape[1] > 0

    def test_affine_grayscale(self):
        """Test affine transformation on grayscale."""
        image = np.ones((100, 100), dtype=np.uint8) * 128
        operator = AffineImage(
            {
                "src_pt1_x": 0,
                "src_pt1_y": 0,
                "src_pt2_x": 100,
                "src_pt2_y": 0,
                "src_pt3_x": 0,
                "src_pt3_y": 100,
                "dst_pt1_x": 0,
                "dst_pt1_y": 0,
                "dst_pt2_x": 100,
                "dst_pt2_y": 0,
                "dst_pt3_x": 0,
                "dst_pt3_y": 100,
            }
        )
        result = operator.compute(image)
        assert result.shape[0] > 0 and result.shape[1] > 0

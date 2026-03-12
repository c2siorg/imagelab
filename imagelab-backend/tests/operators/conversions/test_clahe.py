import cv2
import numpy as np
import pytest

from app.operators.conversions.clahe import CLAHE


class TestCLAHE:
    @pytest.fixture
    def image_bgr(self):
        return np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)

    def test_bgr_input(self, image_bgr):
        operator = CLAHE({})
        result = operator.compute(image_bgr.copy())
        assert result.shape == (100, 100, 3)
        assert result.dtype == np.uint8

    def test_bgra_input(self, image_bgr):
        # Add an alpha channel
        alpha = np.full((100, 100), 128, dtype=np.uint8)
        image_bgra = np.dstack([image_bgr, alpha])
        
        operator = CLAHE({})
        result = operator.compute(image_bgra.copy())
        
        assert result.shape == (100, 100, 4)
        # Alpha should be preserved
        assert np.all(result[:, :, 3] == 128)
        # BGR channels should be processed
        assert not np.array_equal(result[:, :, :3], image_bgr)

    def test_grayscale_input(self):
        image_gray = np.random.randint(0, 256, (100, 100), dtype=np.uint8)
        operator = CLAHE({})
        result = operator.compute(image_gray.copy())
        assert result.shape == (100, 100)
        assert result.dtype == np.uint8

    def test_clip_limit_and_grid_size(self, image_bgr):
        operator = CLAHE({
            "clipLimit": 4.0,
            "tileGridSizeX": 16,
            "tileGridSizeY": 16
        })
        result = operator.compute(image_bgr.copy())
        assert result.shape == (100, 100, 3)

    def test_invalid_dtype_raises(self):
        image_float = np.zeros((100, 100), dtype=np.float32)
        operator = CLAHE({})
        with pytest.raises(ValueError, match="uint8"):
            operator.compute(image_float)

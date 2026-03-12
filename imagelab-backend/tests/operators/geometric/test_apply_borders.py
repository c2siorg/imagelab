import cv2
import numpy as np
import pytest

from app.operators.thresholding.apply_borders import ApplyBorders


class TestApplyBorders:
    @pytest.fixture
    def image(self):
        return np.zeros((100, 100, 3), dtype=np.uint8)

    def test_default_params_identity(self, image):
        # Default is no borders (0,0,0,0)
        operator = ApplyBorders({})
        result = operator.compute(image.copy())
        assert result.shape == (100, 100, 3)
        assert np.array_equal(result, image)

    def test_apply_constant_border(self, image):
        operator = ApplyBorders({
            "borderTop": 10,
            "borderBottom": 20,
            "borderLeft": 30,
            "borderRight": 40,
            "borderColor": "#00FF00" # Green
        })
        result = operator.compute(image.copy())
        assert result.shape == (130, 170, 3)
        # Check green border at top-left corner of result (which is (0,0) in result)
        # hex #00FF00 -> BGR (0, 255, 0)
        assert np.array_equal(result[0, 0], [0, 255, 0])
        # Original image should be at [10:110, 30:130]
        assert np.array_equal(result[10:110, 30:130], image)

    def test_border_all_sides(self, image):
        operator = ApplyBorders({"border_all_sides": 50})
        result = operator.compute(image.copy())
        assert result.shape == (200, 200, 3)

    def test_negative_border_raises_value_error(self, image):
        operator = ApplyBorders({"borderTop": -5})
        with pytest.raises(ValueError, match="non-negative"):
            operator.compute(image)

    def test_border_types(self, image):
        # REFLECT
        operator = ApplyBorders({
            "border_all_sides": 10,
            "borderType": "REFLECT"
        })
        result = operator.compute(image.copy())
        assert result.shape == (120, 120, 3)
        
        # REPLICATE
        operator = ApplyBorders({
            "border_all_sides": 10,
            "borderType": "REPLICATE"
        })
        result = operator.compute(image.copy())
        assert result.shape == (120, 120, 3)

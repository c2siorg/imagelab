import numpy as np
import pytest

from app.operators.thresholding.apply_borders import ApplyBorders


@pytest.fixture
def color_image():
    rng = np.random.default_rng(seed=42)
    return rng.integers(0, 256, (50, 50, 3), dtype=np.uint8)


class TestApplyBordersNegativeClamping:
    def test_negative_all_sides_clamped_to_zero(self, color_image):
        result = ApplyBorders(params={"border_all_sides": -5}).compute(color_image)
        assert result.shape == color_image.shape

    def test_negative_each_side_clamped_to_zero(self, color_image):
        result = ApplyBorders(params={"borderTop": -3, "borderBottom": -1, "borderLeft": 0, "borderRight": 2}).compute(
            color_image
        )
        assert result.shape[0] == color_image.shape[0]
        assert result.shape[1] == color_image.shape[1] + 2


class TestApplyBordersBorderType:
    @pytest.mark.parametrize("border_type", ["CONSTANT", "REFLECT", "REPLICATE", "WRAP"])
    def test_valid_border_types_produce_output(self, color_image, border_type):
        result = ApplyBorders(params={"border_all_sides": 2, "border_type": border_type}).compute(color_image)
        assert result.shape[0] == color_image.shape[0] + 4
        assert result.shape[1] == color_image.shape[1] + 4

    def test_unknown_border_type_raises(self, color_image):
        with pytest.raises(ValueError, match="Unknown border type"):
            ApplyBorders(params={"border_all_sides": 2, "border_type": "INVALID"}).compute(color_image)

    def test_default_border_type_is_constant(self, color_image):
        result = ApplyBorders(params={"border_all_sides": 2}).compute(color_image)
        assert result.shape[0] == color_image.shape[0] + 4


class TestApplyBordersInvalidParams:
    def test_invalid_all_sides_raises(self, color_image):
        with pytest.raises(ValueError):
            ApplyBorders(params={"border_all_sides": "bad"}).compute(color_image)

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


class TestApplyBordersChannels:
    def test_bgra_constant_border_has_opaque_alpha(self):
        bgra = np.full((40, 40, 4), 200, dtype=np.uint8)
        bgra[:, :, 3] = 255
        result = ApplyBorders(params={"border_all_sides": 5, "border_type": "CONSTANT"}).compute(bgra)
        assert result.shape == (50, 50, 4)
        # Check border pixels have black BGR and opaque alpha 255
        np.testing.assert_array_equal(result[0, 0], [0, 0, 0, 255])
        np.testing.assert_array_equal(result[49, 49], [0, 0, 0, 255])
        # Center should remain original
        np.testing.assert_array_equal(result[25, 25], [200, 200, 200, 255])

    def test_single_channel_3d_preserves_shape(self):
        gray_3d = np.full((40, 40, 1), 128, dtype=np.uint8)
        result = ApplyBorders(params={"border_all_sides": 5, "border_type": "CONSTANT"}).compute(gray_3d)
        assert result.shape == (50, 50, 1)
        assert result[0, 0, 0] == 0
        assert result[25, 25, 0] == 128

    def test_grayscale_2d_constant_border(self):
        gray_2d = np.full((40, 40), 128, dtype=np.uint8)
        result = ApplyBorders(params={"border_all_sides": 5, "border_type": "CONSTANT"}).compute(gray_2d)
        assert result.shape == (50, 50)
        assert result[0, 0] == 0
        assert result[25, 25] == 128


class TestApplyBordersExporter:
    def test_exporter_constant_bgra(self):
        import cv2

        from app.services.python_exporter.templates import OPERATOR_TEMPLATES

        template = OPERATOR_TEMPLATES["thresholding_applyborders"]
        code, _ = template({"border_all_sides": 4, "border_type": "CONSTANT"}, "img")
        bgra = np.full((30, 30, 4), 180, dtype=np.uint8)
        bgra[:, :, 3] = 255
        scope = {"cv2": cv2, "np": np, "img": bgra}
        exec("\n".join(code), scope)
        out = scope["img"]
        assert out.shape == (38, 38, 4)
        np.testing.assert_array_equal(out[0, 0], [0, 0, 0, 255])

    def test_exporter_single_channel_3d(self):
        import cv2

        from app.services.python_exporter.templates import OPERATOR_TEMPLATES

        template = OPERATOR_TEMPLATES["thresholding_applyborders"]
        code, _ = template({"border_all_sides": 4, "border_type": "REFLECT"}, "img")
        gray3d = np.full((30, 30, 1), 180, dtype=np.uint8)
        scope = {"cv2": cv2, "np": np, "img": gray3d}
        exec("\n".join(code), scope)
        out = scope["img"]
        assert out.shape == (38, 38, 1)

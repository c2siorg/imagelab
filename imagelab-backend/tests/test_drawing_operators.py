import numpy as np
import pytest

from app.operators.drawing.draw_arrow_line import DrawArrowLine
from app.operators.drawing.draw_circle import DrawCircle
from app.operators.drawing.draw_ellipse import DrawEllipse
from app.operators.drawing.draw_line import DrawLine
from app.operators.drawing.draw_rectangle import DrawRectangle
from app.operators.drawing.draw_text import DrawText


class TestDrawLine:
    def test_default_params_output_shape(self, color_image):
        result = DrawLine({}).compute(color_image)
        assert result.shape == color_image.shape

    def test_output_is_uint8(self, color_image):
        result = DrawLine({}).compute(color_image)
        assert result.dtype == np.uint8

    def test_does_not_modify_original(self, color_image):
        original = color_image.copy()
        DrawLine({"starting_point_x1": 0, "starting_point_y1": 0, "ending_point_x": 50, "ending_point_y": 50}).compute(
            color_image
        )
        np.testing.assert_array_equal(color_image, original)

    def test_line_is_drawn(self):
        blank = np.zeros((100, 100, 3), dtype=np.uint8)
        result = DrawLine(
            {
                "starting_point_x1": 0,
                "starting_point_y1": 50,
                "ending_point_x": 99,
                "ending_point_y": 50,
                "rgbcolors_input": "#ff0000",
                "thickness": 1,
            }
        ).compute(blank)
        assert result[50, :, :].max() > 0

    def test_custom_color_applied(self):
        blank = np.zeros((100, 100, 3), dtype=np.uint8)
        result = DrawLine(
            {
                "starting_point_x1": 0,
                "starting_point_y1": 50,
                "ending_point_x": 99,
                "ending_point_y": 50,
                "rgbcolors_input": "#ff0000",
                "thickness": 3,
            }
        ).compute(blank)
        assert result[50, 50, 2] > 0

    def test_grayscale_input(self, grayscale_image):
        result = DrawLine({}).compute(grayscale_image)
        assert result.shape == grayscale_image.shape
        assert result.dtype == np.uint8


class TestDrawCircle:
    def test_default_params_output_shape(self, color_image):
        result = DrawCircle({}).compute(color_image)
        assert result.shape == color_image.shape

    def test_output_is_uint8(self, color_image):
        result = DrawCircle({}).compute(color_image)
        assert result.dtype == np.uint8

    def test_does_not_modify_original(self, color_image):
        original = color_image.copy()
        DrawCircle({"center_point_x": 50, "center_point_y": 50, "radius": 20}).compute(color_image)
        np.testing.assert_array_equal(color_image, original)

    def test_circle_is_drawn(self):
        blank = np.zeros((100, 100, 3), dtype=np.uint8)
        result = DrawCircle(
            {
                "center_point_x": 50,
                "center_point_y": 50,
                "radius": 20,
                "rgbcolors_input": "#ff0000",
                "thickness": 2,
            }
        ).compute(blank)
        assert result[:, :, 2].max() > 0

    def test_custom_color_applied(self):
        blank = np.zeros((100, 100, 3), dtype=np.uint8)
        result = DrawCircle(
            {
                "center_point_x": 50,
                "center_point_y": 50,
                "radius": 20,
                "rgbcolors_input": "#ff0000",
                "thickness": 2,
            }
        ).compute(blank)
        assert result[:, :, 2].max() > 0

    def test_grayscale_input(self, grayscale_image):
        result = DrawCircle({}).compute(grayscale_image)
        assert result.shape == grayscale_image.shape
        assert result.dtype == np.uint8


class TestDrawEllipse:
    def test_default_params_output_shape(self, color_image):
        result = DrawEllipse({}).compute(color_image)
        assert result.shape == color_image.shape

    def test_output_is_uint8(self, color_image):
        result = DrawEllipse({}).compute(color_image)
        assert result.dtype == np.uint8

    def test_does_not_modify_original(self, color_image):
        original = color_image.copy()
        DrawEllipse({"center_point_x": 50, "center_point_y": 50, "width": 30, "height": 20}).compute(color_image)
        np.testing.assert_array_equal(color_image, original)

    def test_ellipse_is_drawn(self):
        blank = np.zeros((100, 100, 3), dtype=np.uint8)
        result = DrawEllipse(
            {
                "center_point_x": 50,
                "center_point_y": 50,
                "width": 30,
                "height": 20,
                "rgbcolors_input": "#ff0000",
                "thickness": 2,
            }
        ).compute(blank)
        assert result[:, :, 2].max() > 0

    def test_custom_color_applied(self):
        blank = np.zeros((100, 100, 3), dtype=np.uint8)
        result = DrawEllipse(
            {
                "center_point_x": 50,
                "center_point_y": 50,
                "width": 30,
                "height": 20,
                "rgbcolors_input": "#ff0000",
                "thickness": 2,
            }
        ).compute(blank)
        assert result[:, :, 2].max() > 0

    @pytest.mark.xfail(strict=True, reason="Known height/width axes swap bug in DrawEllipse")
    def test_axes_swap_bug(self):
        blank = np.zeros((100, 100, 3), dtype=np.uint8)
        result = DrawEllipse(
            {
                "center_point_x": 50,
                "center_point_y": 50,
                "height": 40,
                "width": 10,
                "rgbcolors_input": "#ffffff",
                "thickness": 1,
            }
        ).compute(blank)
        lit = np.argwhere(result[:, :, 0] > 0)
        row_span = lit[:, 0].max() - lit[:, 0].min()
        col_span = lit[:, 1].max() - lit[:, 1].min()
        assert row_span > col_span

    def test_grayscale_input(self, grayscale_image):
        result = DrawEllipse({}).compute(grayscale_image)
        assert result.shape == grayscale_image.shape
        assert result.dtype == np.uint8


class TestDrawRectangle:
    def test_default_params_output_shape(self, color_image):
        result = DrawRectangle({}).compute(color_image)
        assert result.shape == color_image.shape

    def test_output_is_uint8(self, color_image):
        result = DrawRectangle({}).compute(color_image)
        assert result.dtype == np.uint8

    def test_does_not_modify_original(self, color_image):
        original = color_image.copy()
        DrawRectangle(
            {"starting_point_x": 10, "starting_point_y": 10, "ending_point_x": 50, "ending_point_y": 50}
        ).compute(color_image)
        np.testing.assert_array_equal(color_image, original)

    def test_rectangle_is_drawn(self):
        blank = np.zeros((100, 100, 3), dtype=np.uint8)
        result = DrawRectangle(
            {
                "starting_point_x": 10,
                "starting_point_y": 10,
                "ending_point_x": 50,
                "ending_point_y": 50,
                "rgbcolors_input": "#ff0000",
                "thickness": 2,
            }
        ).compute(blank)
        assert result[:, :, 2].max() > 0

    def test_custom_color_applied(self):
        blank = np.zeros((100, 100, 3), dtype=np.uint8)
        result = DrawRectangle(
            {
                "starting_point_x": 10,
                "starting_point_y": 10,
                "ending_point_x": 50,
                "ending_point_y": 50,
                "rgbcolors_input": "#ff0000",
                "thickness": 2,
            }
        ).compute(blank)
        assert result[:, :, 2].max() > 0

    def test_grayscale_input(self, grayscale_image):
        result = DrawRectangle({}).compute(grayscale_image)
        assert result.shape == grayscale_image.shape
        assert result.dtype == np.uint8


class TestDrawArrowLine:
    def test_default_params_output_shape(self, color_image):
        result = DrawArrowLine({}).compute(color_image)
        assert result.shape == color_image.shape

    def test_output_is_uint8(self, color_image):
        result = DrawArrowLine({}).compute(color_image)
        assert result.dtype == np.uint8

    def test_does_not_modify_original(self, color_image):
        original = color_image.copy()
        DrawArrowLine(
            {"starting_point_x": 0, "starting_point_y": 50, "ending_point_x": 99, "ending_point_y": 50}
        ).compute(color_image)
        np.testing.assert_array_equal(color_image, original)

    def test_arrow_is_drawn(self):
        blank = np.zeros((100, 100, 3), dtype=np.uint8)
        result = DrawArrowLine(
            {
                "starting_point_x": 10,
                "starting_point_y": 50,
                "ending_point_x": 90,
                "ending_point_y": 50,
                "rgbcolors_input": "#ff0000",
                "thickness": 2,
            }
        ).compute(blank)
        assert result[:, :, 2].max() > 0

    def test_custom_color_applied(self):
        blank = np.zeros((100, 100, 3), dtype=np.uint8)
        result = DrawArrowLine(
            {
                "starting_point_x": 10,
                "starting_point_y": 50,
                "ending_point_x": 90,
                "ending_point_y": 50,
                "rgbcolors_input": "#ff0000",
                "thickness": 2,
            }
        ).compute(blank)
        assert result[:, :, 2].max() > 0

    def test_grayscale_input(self, grayscale_image):
        result = DrawArrowLine({}).compute(grayscale_image)
        assert result.shape == grayscale_image.shape
        assert result.dtype == np.uint8


class TestDrawText:
    def test_default_params_output_shape(self, color_image):
        result = DrawText({}).compute(color_image)
        assert result.shape == color_image.shape

    def test_output_is_uint8(self, color_image):
        result = DrawText({}).compute(color_image)
        assert result.dtype == np.uint8

    def test_does_not_modify_original(self, color_image):
        original = color_image.copy()
        DrawText({"draw_text": "Test", "starting_point_x": 10, "starting_point_y": 50}).compute(color_image)
        np.testing.assert_array_equal(color_image, original)

    def test_text_is_drawn(self):
        blank = np.zeros((100, 100, 3), dtype=np.uint8)
        result = DrawText(
            {
                "draw_text": "Test",
                "starting_point_x": 10,
                "starting_point_y": 50,
                "rgbcolors_input": "#ff0000",
                "scale": 1,
                "thickness": 2,
            }
        ).compute(blank)
        assert result[:, :, 2].max() > 0

    def test_custom_color_applied(self):
        blank = np.zeros((100, 100, 3), dtype=np.uint8)
        result = DrawText(
            {
                "draw_text": "Test",
                "starting_point_x": 10,
                "starting_point_y": 50,
                "rgbcolors_input": "#ff0000",
                "scale": 1,
                "thickness": 2,
            }
        ).compute(blank)
        assert result[:, :, 2].max() > 0

    def test_empty_string_does_not_crash(self, color_image):
        result = DrawText({"draw_text": ""}).compute(color_image)
        assert result.shape == color_image.shape

    def test_custom_text_content(self, color_image):
        result1 = DrawText({"draw_text": "Hello", "starting_point_x": 10, "starting_point_y": 50}).compute(
            color_image.copy()
        )
        result2 = DrawText({"draw_text": "World", "starting_point_x": 10, "starting_point_y": 50}).compute(
            color_image.copy()
        )
        assert not np.array_equal(result1, result2)

    def test_grayscale_input(self, grayscale_image):
        result = DrawText({}).compute(grayscale_image)
        assert result.shape == grayscale_image.shape
        assert result.dtype == np.uint8

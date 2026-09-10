import numpy as np

from app.operators.drawing.draw_text import DrawText


class TestDrawTextDefaultY:
    def test_default_params_render_visible_text(self):
        img = np.zeros((100, 200, 3), dtype=np.uint8)
        result = DrawText(params={}).compute(img)
        assert not np.array_equal(result, img), "DrawText with default params must render visible text"


class TestDrawTextOutputShape:
    def test_output_shape_matches_input(self):
        img = np.zeros((100, 200, 3), dtype=np.uint8)
        result = DrawText(params={}).compute(img)
        assert result.shape == img.shape

    def test_does_not_mutate_input(self):
        img = np.zeros((100, 200, 3), dtype=np.uint8)
        original = img.copy()
        DrawText(params={}).compute(img)
        np.testing.assert_array_equal(img, original)


class TestDrawTextParams:
    def test_custom_text_renders(self):
        img = np.zeros((100, 200, 3), dtype=np.uint8)
        result = DrawText(params={"draw_text": "Hello", "starting_point_y": 50}).compute(img)
        assert not np.array_equal(result, img)

    def test_scale_two_default_y_renders_visible(self):
        img = np.zeros((200, 200, 3), dtype=np.uint8)
        result = DrawText(params={"scale": 2}).compute(img)
        assert not np.array_equal(result, img), "scale=2 with default y must still render visible text"

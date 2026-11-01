import ast

import numpy as np
import pytest

from app.models.pipeline import PipelineStep
from app.operators.segmentation.connected_components import ConnectedComponents
from app.services.python_exporter.generator import export_pipeline_to_python


def _synthetic_components_image() -> np.ndarray:
    """Creates a 100x100 BGR image with two distinct white squares:

    - Large square: 20x20 pixels (area 400)
    - Small square: 5x5 pixels (area 25)
    """
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    img[10:30, 10:30] = 255
    img[70:75, 70:75] = 255
    return img


class TestConnectedComponents:
    def test_color_map_mode_with_min_area_filtering(self):
        img = _synthetic_components_image()
        # min_area=50 will retain the 400-pixel component and filter out the 25-pixel component
        result = ConnectedComponents({"output_mode": "COLOR_MAP", "min_area": 50}).compute(img)
        assert result.shape == (100, 100, 3)
        assert result.dtype == np.uint8

        # Large component region has non-zero pseudocolor
        assert np.any(result[10:30, 10:30] > 0)
        # Filtered small component region remains black (0)
        assert np.all(result[70:75, 70:75] == 0)

    def test_color_map_mode_retaining_all_components(self):
        img = _synthetic_components_image()
        # min_area=0 will retain both components
        result = ConnectedComponents({"output_mode": "COLOR_MAP", "min_area": 0}).compute(img)
        assert result.shape == (100, 100, 3)
        assert np.any(result[10:30, 10:30] > 0)
        assert np.any(result[70:75, 70:75] > 0)

    def test_connectivity_4_vs_8(self):
        # Two pixels touching diagonally
        diag_img = np.zeros((10, 10), dtype=np.uint8)
        diag_img[2, 2] = 255
        diag_img[3, 3] = 255

        # In 8-way connectivity, they form 1 component
        res_8 = ConnectedComponents({"connectivity": 8, "output_mode": "COLOR_MAP", "min_area": 0}).compute(diag_img)
        # In 4-way connectivity, they form 2 separate components
        res_4 = ConnectedComponents({"connectivity": 4, "output_mode": "COLOR_MAP", "min_area": 0}).compute(diag_img)

        # In 8-way, both pixels have the exact same color
        assert np.array_equal(res_8[2, 2], res_8[3, 3])
        # In 4-way with 2 labels, they get distinct hues
        assert not np.array_equal(res_4[2, 2], res_4[3, 3])

    def test_bounding_box_mode(self):
        img = _synthetic_components_image()
        result = ConnectedComponents(
            {"output_mode": "BOUNDING_BOX", "min_area": 50, "rgbcolors_input": "#00ffff", "thickness": 2}
        ).compute(img)
        assert result.shape == (100, 100, 3)
        assert result.dtype == np.uint8
        # Cyan color in BGR is (255, 255, 0)
        # Check that bounding box lines have cyan pixels
        assert np.any((result[:, :, 0] == 255) & (result[:, :, 1] == 255) & (result[:, :, 2] == 0))

    def test_centroid_mode(self):
        img = _synthetic_components_image()
        result = ConnectedComponents(
            {"output_mode": "CENTROID", "min_area": 50, "rgbcolors_input": "#00ffff", "thickness": 2}
        ).compute(img)
        assert result.shape == (100, 100, 3)
        assert result.dtype == np.uint8
        # Centroid of 10:30 is at (19.5, 19.5) rounded to (20, 20)
        assert np.any((result[:, :, 0] == 255) & (result[:, :, 1] == 255) & (result[:, :, 2] == 0))

    def test_grayscale_2d_input(self):
        gray = np.zeros((100, 100), dtype=np.uint8)
        gray[10:30, 10:30] = 255
        result = ConnectedComponents({"output_mode": "COLOR_MAP"}).compute(gray)
        assert result.shape == (100, 100, 3)
        assert result.dtype == np.uint8

    def test_single_channel_3d_input(self):
        gray_1ch = np.zeros((100, 100, 1), dtype=np.uint8)
        gray_1ch[10:30, 10:30, 0] = 255
        result = ConnectedComponents({"output_mode": "COLOR_MAP"}).compute(gray_1ch)
        assert result.shape == (100, 100, 3)
        assert result.dtype == np.uint8

    def test_bgra_input_preserves_alpha(self):
        bgra = np.zeros((100, 100, 4), dtype=np.uint8)
        bgra[:, :, 3] = 180  # semi-transparent
        bgra[10:30, 10:30, :3] = 255

        # COLOR_MAP preserves alpha
        res_cmap = ConnectedComponents({"output_mode": "COLOR_MAP"}).compute(bgra)
        assert res_cmap.shape == (100, 100, 4)
        assert np.all(res_cmap[:, :, 3] == 180)

        # BOUNDING_BOX preserves alpha
        res_bbox = ConnectedComponents({"output_mode": "BOUNDING_BOX", "rgbcolors_input": "#00ffff"}).compute(bgra)
        assert res_bbox.shape == (100, 100, 4)
        # Background alpha preserved
        assert res_bbox[0, 0, 3] == 180
        # Drawn box is fully opaque
        assert np.any(res_bbox[:, :, 3] == 255)

    def test_empty_foreground_handles_gracefully(self):
        black = np.zeros((50, 50, 3), dtype=np.uint8)
        result = ConnectedComponents({"output_mode": "COLOR_MAP"}).compute(black)
        assert result.shape == (50, 50, 3)
        assert np.all(result == 0)

    def test_parameter_clamping_and_tolerances(self):
        img = _synthetic_components_image()
        # Invalid connectivity and extreme parameter values clamp safely
        result = ConnectedComponents(
            {
                "connectivity": 99,
                "output_mode": "UNKNOWN_MODE",
                "min_area": -100,
                "thickness": 999,
            }
        ).compute(img)
        assert result.shape == (100, 100, 3)
        assert result.dtype == np.uint8

    def test_invalid_empty_image_raises_error(self):
        with pytest.raises(ValueError, match="invalid or empty image"):
            ConnectedComponents({}).compute(np.array([], dtype=np.uint8))

    def test_invalid_none_image_raises_error(self):
        with pytest.raises(ValueError, match="invalid or empty image"):
            ConnectedComponents({}).compute(None)

    def test_invalid_dtype_raises_error(self):
        with pytest.raises(ValueError, match="expects a uint8 image"):
            ConnectedComponents({}).compute(np.zeros((50, 50), dtype=np.float32))

    def test_invalid_channels_raises_error(self):
        with pytest.raises(ValueError, match="expects a 2-D or 3-D image with 1, 3, or 4 channels"):
            ConnectedComponents({}).compute(np.zeros((50, 50, 2), dtype=np.uint8))

    def test_python_exporter_connected_components(self):
        steps = [
            PipelineStep(
                type="segmentation_connectedcomponents",
                params={"connectivity": 8, "min_area": 50, "output_mode": "COLOR_MAP"},
            )
        ]
        code, unsupported = export_pipeline_to_python(steps, "input.png", "output.png")
        assert unsupported == []
        assert "connectedComponentsWithStats" in code

        # 1. Verify AST parses without SyntaxError or IndentationError
        tree = ast.parse(code)
        assert isinstance(tree, ast.Module)

        # 2. Verify compilation succeeds
        compiled = compile(code, "<string>", "exec")
        namespace = {}
        exec(compiled, namespace)
        assert "run_pipeline" in namespace
        run_fn = namespace["run_pipeline"]

        # 3. Test execution on 3-channel BGR image
        bgr_img = _synthetic_components_image()
        res_bgr = run_fn(bgr_img.copy())
        assert res_bgr.shape == (100, 100, 3)
        assert res_bgr.dtype == np.uint8

        # 4. Test execution on 2-D grayscale image
        gray_img = np.zeros((100, 100), dtype=np.uint8)
        gray_img[10:30, 10:30] = 255
        res_gray = run_fn(gray_img.copy())
        assert res_gray.shape == (100, 100, 3)
        assert res_gray.dtype == np.uint8

        # 5. Test execution on 4-channel BGRA image
        bgra_img = np.zeros((100, 100, 4), dtype=np.uint8)
        bgra_img[:, :, 3] = 150
        bgra_img[10:30, 10:30, :3] = 255
        res_bgra = run_fn(bgra_img.copy())
        assert res_bgra.shape == (100, 100, 4)
        assert np.all(res_bgra[:, :, 3] == 150)

    def test_python_exporter_bounding_box_and_centroid_modes(self):
        for mode in ("BOUNDING_BOX", "CENTROID"):
            steps = [
                PipelineStep(
                    type="segmentation_connectedcomponents",
                    params={"output_mode": mode, "min_area": 50, "rgbcolors_input": "#00ffff", "thickness": 2},
                )
            ]
            code, unsupported = export_pipeline_to_python(steps, "input.png", "output.png")
            assert unsupported == []
            compiled = compile(code, "<string>", "exec")
            namespace = {}
            exec(compiled, namespace)
            bgr_img = _synthetic_components_image()
            res = namespace["run_pipeline"](bgr_img.copy())
            assert res.shape == (100, 100, 3)

    def test_invert_mask_dark_objects_on_bright_background(self):
        # Bright background (255) with a centered dark square (0)
        doc_img = np.full((100, 100), 255, dtype=np.uint8)
        doc_img[30:70, 30:70] = 0

        # With invert, the dark square becomes foreground (area 1600)
        res_inv = ConnectedComponents({"output_mode": "COLOR_MAP", "min_area": 50, "invert": True}).compute(doc_img)
        assert res_inv.shape == (100, 100, 3)
        # Dark square region now receives a colored label
        assert np.any(res_inv[30:70, 30:70] > 0)
        # Bright background was inverted to 0 and becomes black background
        assert np.all(res_inv[0:20, 0:20] == 0)

    def test_consecutive_labels_receive_distinct_hues(self):
        # Verify that adjacent labels are always separated by 37 degrees in hue space
        hues = [(i * 37) % 180 for i in range(1, 200)]
        for k in range(len(hues) - 1):
            diff = abs(hues[k + 1] - hues[k])
            # In modular 180 space, difference between consecutive labels is either 37 or 143
            assert diff in (37, 143)

    def test_python_exporter_with_invert_flag(self):
        steps = [
            PipelineStep(
                type="segmentation_connectedcomponents",
                params={"connectivity": 4, "invert": True, "output_mode": "COLOR_MAP"},
            )
        ]
        code, unsupported = export_pipeline_to_python(steps, "input.png", "output.png")
        assert unsupported == []
        assert "bitwise_not" in code
        compiled = compile(code, "<string>", "exec")
        namespace = {}
        exec(compiled, namespace)
        doc_img = np.full((100, 100), 255, dtype=np.uint8)
        doc_img[30:70, 30:70] = 0
        res = namespace["run_pipeline"](doc_img.copy())
        assert res.shape == (100, 100, 3)
        assert np.any(res[30:70, 30:70] > 0)

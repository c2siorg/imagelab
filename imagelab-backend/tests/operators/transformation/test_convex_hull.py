import ast

import cv2
import numpy as np
import pytest

from app.models.pipeline import PipelineStep
from app.operators.transformation.convex_hull import ConvexHull
from app.services.python_exporter.generator import export_pipeline_to_python


def _synthetic_star_image() -> np.ndarray:
    """Creates a 120x120 binary shape with clear concavities (star polygon)."""
    img = np.zeros((120, 120), dtype=np.uint8)
    pts = np.array(
        [
            [60, 15],
            [72, 45],
            [105, 45],
            [78, 65],
            [88, 98],
            [60, 78],
            [32, 98],
            [42, 65],
            [15, 45],
            [48, 45],
        ],
        dtype=np.int32,
    )
    cv2.fillPoly(img, [pts], 255)
    return img


class TestConvexHull:
    def test_hull_and_defects_mode(self):
        star = _synthetic_star_image()
        bgr = cv2.cvtColor(star, cv2.COLOR_GRAY2BGR)
        op = ConvexHull(
            {
                "mode": "HULL_AND_DEFECTS",
                "min_area": 50,
                "min_defect_depth": 2.0,
                "hull_color": "#00ffff",
                "defect_color": "#ff0000",
                "thickness": 2,
            }
        )
        result = op.compute(bgr)
        assert result.shape == (120, 120, 3)
        assert result.dtype == np.uint8
        # Hull color is cyan (#00ffff -> BGR (255, 255, 0))
        assert np.any((result[:, :, 0] == 255) & (result[:, :, 1] == 255) & (result[:, :, 2] == 0))
        # Defect color is red (#ff0000 -> BGR (0, 0, 255))
        assert np.any((result[:, :, 2] == 255) & (result[:, :, 0] == 0) & (result[:, :, 1] == 0))

    def test_hull_only_mode(self):
        star = _synthetic_star_image()
        bgr = cv2.cvtColor(star, cv2.COLOR_GRAY2BGR)
        op = ConvexHull(
            {
                "mode": "HULL_ONLY",
                "min_area": 50,
                "hull_color": "#00ffff",
                "defect_color": "#ff0000",
                "thickness": 2,
            }
        )
        result = op.compute(bgr)
        assert result.shape == (120, 120, 3)
        # Hull cyan lines present
        assert np.any((result[:, :, 0] == 255) & (result[:, :, 1] == 255) & (result[:, :, 2] == 0))
        # No defect red markers drawn
        assert not np.any((result[:, :, 2] == 255) & (result[:, :, 0] == 0) & (result[:, :, 1] == 0))

    def test_min_area_filtering(self):
        # Image with small noise spot (area ~4) and large star
        star = _synthetic_star_image()
        star[5:7, 5:7] = 255
        bgr = cv2.cvtColor(star, cv2.COLOR_GRAY2BGR)
        # Area threshold set high so small spot is ignored
        op = ConvexHull({"min_area": 50, "hull_color": "#00ffff"})
        result = op.compute(bgr)
        assert result.shape == (120, 120, 3)
        # Around (5, 5), no hull lines should be drawn
        assert np.all(result[4:8, 4:8, 0] == result[4:8, 4:8, 1])

    def test_min_defect_depth_threshold(self):
        star = _synthetic_star_image()
        bgr = cv2.cvtColor(star, cv2.COLOR_GRAY2BGR)
        # Extremely high defect depth filters out all defects
        op = ConvexHull(
            {
                "mode": "HULL_AND_DEFECTS",
                "min_defect_depth": 300.0,
                "hull_color": "#00ffff",
                "defect_color": "#ff0000",
            }
        )
        result = op.compute(bgr)
        # No defect red points drawn
        assert not np.any((result[:, :, 2] == 255) & (result[:, :, 0] == 0) & (result[:, :, 1] == 0))

    def test_show_contours_flag(self):
        star = _synthetic_star_image()
        bgr = cv2.cvtColor(star, cv2.COLOR_GRAY2BGR)
        op_without = ConvexHull({"show_contours": False, "hull_color": "#00ffff"})
        res_without = op_without.compute(bgr)

        op_with = ConvexHull({"show_contours": True, "hull_color": "#00ffff"})
        res_with = op_with.compute(bgr)

        # res_with should contain contour draw color (200, 200, 200)
        assert np.any((res_with[:, :, 0] == 200) & (res_with[:, :, 1] == 200) & (res_with[:, :, 2] == 200))
        assert not np.array_equal(res_without, res_with)

    def test_2d_grayscale_input_preserves_single_channel(self):
        star = _synthetic_star_image()
        op = ConvexHull({"min_area": 50})
        result = op.compute(star)
        assert result.ndim == 2
        assert result.shape == (120, 120)
        assert result.dtype == np.uint8

    def test_3d_single_channel_input_preserves_single_channel(self):
        star = _synthetic_star_image()[:, :, np.newaxis]
        op = ConvexHull({"min_area": 50})
        result = op.compute(star)
        assert result.ndim == 3
        assert result.shape == (120, 120, 1)
        assert result.dtype == np.uint8

    def test_bgra_preserves_alpha_channel(self):
        star = _synthetic_star_image()
        bgra = np.zeros((120, 120, 4), dtype=np.uint8)
        bgra[:, :, 3] = 160  # semi-transparent base
        bgra[star > 0, :3] = 255
        op = ConvexHull(
            {
                "mode": "HULL_AND_DEFECTS",
                "min_area": 50,
                "hull_color": "#00ffff",
                "defect_color": "#ff0000",
            }
        )
        result = op.compute(bgra)
        assert result.shape == (120, 120, 4)
        assert result.dtype == np.uint8
        # Unmodified corners retain original alpha
        assert result[0, 0, 3] == 160
        # Annotated pixels have full opacity 255
        assert np.any(result[:, :, 3] == 255)

    def test_blank_image_no_contours(self):
        blank = np.zeros((100, 100, 3), dtype=np.uint8)
        op = ConvexHull({})
        result = op.compute(blank)
        assert result.shape == (100, 100, 3)
        assert np.all(result == 0)

    def test_invalid_parameters_clamping(self):
        star = _synthetic_star_image()
        # Pass negative or extreme values; operator should not crash
        op = ConvexHull(
            {
                "mode": "INVALID_MODE",
                "min_area": -10,
                "min_defect_depth": -5.0,
                "thickness": 999,
                "hull_color": "not-a-color",
            }
        )
        result = op.compute(star)
        assert result.shape == (120, 120)
        assert result.dtype == np.uint8

    def test_float_string_parameter_parsing(self):
        star = _synthetic_star_image()
        # Ensure float strings like "60.0" parse properly rather than reverting to defaults
        op = ConvexHull(
            {
                "min_area": "60.0",
                "min_defect_depth": "3.5",
                "thickness": "3.0",
                "hull_color": "#00ffff",
            }
        )
        res = op.compute(star)
        assert res.shape == (120, 120)

    def test_non_monotonic_hull_indices_defects(self):
        # Contour whose raw cv2.convexHull indices are non-monotonic
        img = np.zeros((100, 100), dtype=np.uint8)
        pts = np.array(
            [[66, 35], [50, 44], [72, 34], [84, 47], [11, 16], [43, 26], [52, 68], [60, 63]],
            dtype=np.int32,
        )
        cv2.fillPoly(img, [pts], 255)
        bgr = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        op = ConvexHull({"mode": "HULL_AND_DEFECTS", "min_defect_depth": 1.0, "defect_color": "#ff0000"})
        res = op.compute(bgr)
        # Assert red defect indicators are drawn
        assert np.any((res[:, :, 2] == 255) & (res[:, :, 0] == 0) & (res[:, :, 1] == 0))

    def test_collinear_and_degenerate_contours_do_not_crash(self):
        # 1-pixel thin line shape, 1-pixel dot, and 2-pixel contour
        canvas = np.zeros((64, 64, 3), dtype=np.uint8)
        canvas[20, 10:40] = [255, 255, 255]  # collinear 1-pixel line
        canvas[10, 10] = [255, 255, 255]  # 1-point dot
        canvas[50, 20:22] = [255, 255, 255]  # 2-point contour

        for mode in ("HULL_ONLY", "HULL_AND_DEFECTS"):
            op = ConvexHull({"mode": mode, "min_area": 0, "show_contours": True})
            result = op.compute(canvas)
            assert result.shape == (64, 64, 3)
            assert result.dtype == np.uint8

    def test_error_handling(self):
        op = ConvexHull({})
        with pytest.raises(ValueError, match="invalid or empty image"):
            op.compute(None)  # type: ignore

        with pytest.raises(ValueError, match="invalid or empty image"):
            op.compute(np.array([], dtype=np.uint8))

        with pytest.raises(ValueError, match="uint8"):
            op.compute(np.zeros((50, 50), dtype=np.float32))

        with pytest.raises(ValueError, match="channels"):
            op.compute(np.zeros((50, 50, 5), dtype=np.uint8))


class TestConvexHullExporter:
    def test_exporter_script_generation_and_execution(self):
        steps = [
            PipelineStep(
                block_id="step1",
                type="transformation_convexhull",
                params={
                    "mode": "HULL_AND_DEFECTS",
                    "min_area": 50,
                    "min_defect_depth": 3.0,
                    "hull_color": "#00ffff",
                    "defect_color": "#ff0000",
                    "thickness": 2,
                    "show_contours": True,
                },
            )
        ]
        script, _ = export_pipeline_to_python(steps, pipeline_name="Convex Hull Test")
        assert "transformation_convexhull" in script
        # Check AST validity
        parsed = ast.parse(script)
        assert parsed is not None

        # Execute the generated script in an isolated namespace
        star = _synthetic_star_image()
        bgr = cv2.cvtColor(star, cv2.COLOR_GRAY2BGR)
        scope = {}
        exec(script, scope)
        run_fn = scope.get("run_pipeline")
        assert callable(run_fn)

        out = run_fn(bgr.copy())
        assert out.shape == (120, 120, 3)
        assert out.dtype == np.uint8
        # Verify cyan hull points drawn
        assert np.any((out[:, :, 0] == 255) & (out[:, :, 1] == 255) & (out[:, :, 2] == 0))
        # Verify red defect points drawn
        assert np.any((out[:, :, 2] == 255) & (out[:, :, 0] == 0) & (out[:, :, 1] == 0))

        # Pixel equivalence test between operator compute and exported script execution
        expected = ConvexHull(steps[0].params).compute(bgr.copy())
        assert np.array_equal(out, expected)

    def test_exporter_on_grayscale_and_bgra(self):
        steps = [
            PipelineStep(
                block_id="step1",
                type="transformation_convexhull",
                params={"mode": "HULL_ONLY", "min_area": 50},
            )
        ]
        script, _ = export_pipeline_to_python(steps)
        scope = {}
        exec(script, scope)
        run_fn = scope["run_pipeline"]

        # Grayscale input
        star = _synthetic_star_image()
        out_gray = run_fn(star.copy())
        assert out_gray.shape == (120, 120)
        expected_gray = ConvexHull(steps[0].params).compute(star.copy())
        assert np.array_equal(out_gray, expected_gray)

        # BGRA input
        bgra = np.zeros((120, 120, 4), dtype=np.uint8)
        bgra[star > 0, :3] = 255
        bgra[:, :, 3] = 200
        out_bgra = run_fn(bgra.copy())
        assert out_bgra.shape == (120, 120, 4)
        expected_bgra = ConvexHull(steps[0].params).compute(bgra.copy())
        assert np.array_equal(out_bgra, expected_bgra)

    def test_exporter_pixel_equivalence_hull_and_defects_all_channels(self):
        params = {
            "mode": "HULL_AND_DEFECTS",
            "min_area": 40,
            "min_defect_depth": 2.5,
            "hull_color": "#00ffff",
            "defect_color": "#ff0000",
            "thickness": 3,
            "show_contours": True,
        }
        steps = [PipelineStep(block_id="s1", type="transformation_convexhull", params=params)]
        script, _ = export_pipeline_to_python(steps)
        scope = {}
        exec(script, scope)
        run_fn = scope["run_pipeline"]
        op = ConvexHull(params)

        star = _synthetic_star_image()
        # Test 2D Grayscale
        assert np.array_equal(run_fn(star.copy()), op.compute(star.copy()))

        # Test 3-channel BGR
        bgr = cv2.cvtColor(star, cv2.COLOR_GRAY2BGR)
        assert np.array_equal(run_fn(bgr.copy()), op.compute(bgr.copy()))

        # Test 4-channel BGRA
        bgra = np.zeros((120, 120, 4), dtype=np.uint8)
        bgra[star > 0, :3] = 255
        bgra[:, :, 3] = 180
        assert np.array_equal(run_fn(bgra.copy()), op.compute(bgra.copy()))

    def test_exporter_does_not_mutate_input_buffer(self):
        star = _synthetic_star_image()
        bgr = cv2.cvtColor(star, cv2.COLOR_GRAY2BGR)
        bgr_clone = bgr.copy()
        steps = [
            PipelineStep(
                block_id="s1",
                type="transformation_convexhull",
                params={"mode": "HULL_AND_DEFECTS", "min_area": 50},
            )
        ]
        script, _ = export_pipeline_to_python(steps)
        scope = {}
        exec(script, scope)
        run_fn = scope["run_pipeline"]
        run_fn(bgr)
        # Verify original array passed into run_pipeline was not modified in-place
        np.testing.assert_array_equal(bgr, bgr_clone)

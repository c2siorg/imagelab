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

    def test_2d_grayscale_input_converts_to_bgr(self):
        star = _synthetic_star_image()
        op = ConvexHull({"min_area": 50})
        result = op.compute(star)
        assert result.ndim == 3
        assert result.shape == (120, 120, 3)
        assert result.dtype == np.uint8

    def test_3d_single_channel_input(self):
        star = _synthetic_star_image()[:, :, np.newaxis]
        op = ConvexHull({"min_area": 50})
        result = op.compute(star)
        assert result.ndim == 3
        assert result.shape == (120, 120, 3)
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
        assert result.shape == (120, 120, 3)
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

        out = run_fn(bgr)
        assert out.shape == (120, 120, 3)
        assert out.dtype == np.uint8
        # Verify cyan hull points drawn
        assert np.any((out[:, :, 0] == 255) & (out[:, :, 1] == 255) & (out[:, :, 2] == 0))
        # Verify red defect points drawn
        assert np.any((out[:, :, 2] == 255) & (out[:, :, 0] == 0) & (out[:, :, 1] == 0))

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
        out_gray = run_fn(star)
        assert out_gray.shape == (120, 120, 3)

        # BGRA input
        bgra = np.zeros((120, 120, 4), dtype=np.uint8)
        bgra[star > 0, :3] = 255
        bgra[:, :, 3] = 200
        out_bgra = run_fn(bgra)
        assert out_bgra.shape == (120, 120, 4)

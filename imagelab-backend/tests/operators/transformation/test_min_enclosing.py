import ast

import cv2
import numpy as np
import pytest

from app.models.pipeline import PipelineStep
from app.operators.transformation.min_enclosing import MinEnclosing
from app.services.python_exporter.generator import export_pipeline_to_python


def _synthetic_star_image() -> np.ndarray:
    """Creates a 120x120 binary shape with clear orientation and concavities."""
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


class TestMinEnclosing:
    def test_rotated_box_mode(self):
        star = _synthetic_star_image()
        bgr = cv2.cvtColor(star, cv2.COLOR_GRAY2BGR)
        op = MinEnclosing(
            {
                "geometry": "ROTATED_BOX",
                "min_area": 50,
                "box_color": "#00ffff",
                "thickness": 2,
            }
        )
        result = op.compute(bgr)
        assert result.shape == (120, 120, 3)
        assert result.dtype == np.uint8
        # Box color is cyan (#00ffff -> BGR (255, 255, 0))
        assert np.any((result[:, :, 0] == 255) & (result[:, :, 1] == 255) & (result[:, :, 2] == 0))

    def test_enclosing_circle_mode(self):
        star = _synthetic_star_image()
        bgr = cv2.cvtColor(star, cv2.COLOR_GRAY2BGR)
        op = MinEnclosing(
            {
                "geometry": "ENCLOSING_CIRCLE",
                "min_area": 50,
                "circle_color": "#ff00ff",
                "thickness": 2,
            }
        )
        result = op.compute(bgr)
        assert result.shape == (120, 120, 3)
        # Circle color is magenta (#ff00ff -> BGR (255, 0, 255))
        assert np.any((result[:, :, 0] == 255) & (result[:, :, 1] == 0) & (result[:, :, 2] == 255))

    def test_fit_ellipse_mode(self):
        star = _synthetic_star_image()
        bgr = cv2.cvtColor(star, cv2.COLOR_GRAY2BGR)
        op = MinEnclosing(
            {
                "geometry": "FIT_ELLIPSE",
                "min_area": 50,
                "ellipse_color": "#ffff00",
                "thickness": 2,
            }
        )
        result = op.compute(bgr)
        assert result.shape == (120, 120, 3)
        # Ellipse color is yellow (#ffff00 -> BGR (0, 255, 255))
        assert np.any((result[:, :, 0] == 0) & (result[:, :, 1] == 255) & (result[:, :, 2] == 255))

    def test_all_shapes_mode(self):
        star = _synthetic_star_image()
        bgr = cv2.cvtColor(star, cv2.COLOR_GRAY2BGR)
        op = MinEnclosing(
            {
                "geometry": "ALL_SHAPES",
                "min_area": 50,
                "box_color": "#00ffff",
                "circle_color": "#ff00ff",
                "ellipse_color": "#ffff00",
                "thickness": 2,
            }
        )
        result = op.compute(bgr)
        assert result.shape == (120, 120, 3)
        # Verify box (cyan) is drawn
        assert np.any((result[:, :, 0] == 255) & (result[:, :, 1] == 255) & (result[:, :, 2] == 0))
        # Verify circle (magenta) is drawn
        assert np.any((result[:, :, 0] == 255) & (result[:, :, 1] == 0) & (result[:, :, 2] == 255))
        # Verify ellipse (yellow) is drawn
        assert np.any((result[:, :, 0] == 0) & (result[:, :, 1] == 255) & (result[:, :, 2] == 255))

    def test_min_area_filtering(self):
        # Image with small noise spot (area ~4) and large star
        star = _synthetic_star_image()
        star[5:7, 5:7] = 255
        bgr = cv2.cvtColor(star, cv2.COLOR_GRAY2BGR)
        op = MinEnclosing({"min_area": 50, "box_color": "#00ffff"})
        result = op.compute(bgr)
        assert result.shape == (120, 120, 3)
        # Around (5, 5), no box lines should be drawn
        assert np.all(result[4:8, 4:8, 0] == result[4:8, 4:8, 1])

    def test_show_contours_flag(self):
        star = _synthetic_star_image()
        bgr = cv2.cvtColor(star, cv2.COLOR_GRAY2BGR)
        op_without = MinEnclosing({"show_contours": False, "box_color": "#00ffff"})
        res_without = op_without.compute(bgr)

        op_with = MinEnclosing({"show_contours": True, "box_color": "#00ffff"})
        res_with = op_with.compute(bgr)

        # res_with should contain contour draw color (128, 128, 128)
        assert np.any((res_with[:, :, 0] == 128) & (res_with[:, :, 1] == 128) & (res_with[:, :, 2] == 128))
        assert not np.array_equal(res_without, res_with)

    def test_2d_grayscale_input_preserves_single_channel(self):
        star = _synthetic_star_image()
        op = MinEnclosing({"min_area": 50})
        result = op.compute(star)
        assert result.ndim == 2
        assert result.shape == (120, 120)
        assert result.dtype == np.uint8

    def test_3d_single_channel_input_preserves_single_channel(self):
        star = _synthetic_star_image()[:, :, np.newaxis]
        op = MinEnclosing({"min_area": 50})
        result = op.compute(star)
        assert result.ndim == 3
        assert result.shape == (120, 120, 1)
        assert result.dtype == np.uint8

    def test_bgra_preserves_alpha_channel(self):
        star = _synthetic_star_image()
        bgra = np.zeros((120, 120, 4), dtype=np.uint8)
        bgra[:, :, 3] = 160  # semi-transparent base
        bgra[star > 0, :3] = 255
        op = MinEnclosing(
            {
                "geometry": "ROTATED_BOX",
                "min_area": 50,
                "box_color": "#00ffff",
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
        op = MinEnclosing({})
        result = op.compute(blank)
        assert result.shape == (100, 100, 3)
        assert np.all(result == 0)

    def test_invalid_parameters_clamping(self):
        star = _synthetic_star_image()
        # Pass negative or extreme values and float strings
        op = MinEnclosing(
            {
                "geometry": "INVALID_GEOMETRY",
                "min_area": "60.0",
                "thickness": "3.0",
                "box_color": "not-a-color",
            }
        )
        result = op.compute(star)
        assert result.shape == (120, 120)
        assert result.dtype == np.uint8

    def test_error_handling(self):
        op = MinEnclosing({})
        with pytest.raises(ValueError, match="invalid or empty image"):
            op.compute(None)  # type: ignore

        with pytest.raises(ValueError, match="invalid or empty image"):
            op.compute(np.array([], dtype=np.uint8))

        with pytest.raises(ValueError, match="uint8"):
            op.compute(np.zeros((50, 50), dtype=np.float32))

        with pytest.raises(ValueError, match="channels"):
            op.compute(np.zeros((50, 50, 5), dtype=np.uint8))


class TestMinEnclosingExporter:
    def test_exporter_script_generation_and_execution(self):
        steps = [
            PipelineStep(
                block_id="step1",
                type="transformation_minenclosing",
                params={
                    "geometry": "ALL_SHAPES",
                    "min_area": 50,
                    "box_color": "#00ffff",
                    "circle_color": "#ff00ff",
                    "ellipse_color": "#ffff00",
                    "thickness": 2,
                    "show_contours": True,
                },
            )
        ]
        script, _ = export_pipeline_to_python(steps, pipeline_name="Min Enclosing Test")
        assert "transformation_minenclosing" in script
        parsed = ast.parse(script)
        assert parsed is not None

        star = _synthetic_star_image()
        bgr = cv2.cvtColor(star, cv2.COLOR_GRAY2BGR)
        scope = {}
        exec(script, scope)
        run_fn = scope.get("run_pipeline")
        assert callable(run_fn)

        out = run_fn(bgr.copy())
        assert out.shape == (120, 120, 3)
        assert out.dtype == np.uint8

        expected = MinEnclosing(steps[0].params).compute(bgr.copy())
        assert np.array_equal(out, expected)

    def test_exporter_on_grayscale_and_bgra(self):
        steps = [
            PipelineStep(
                block_id="step1",
                type="transformation_minenclosing",
                params={"geometry": "ROTATED_BOX", "min_area": 50},
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
        expected_gray = MinEnclosing(steps[0].params).compute(star.copy())
        assert np.array_equal(out_gray, expected_gray)

        # BGRA input
        bgra = np.zeros((120, 120, 4), dtype=np.uint8)
        bgra[star > 0, :3] = 255
        bgra[:, :, 3] = 200
        out_bgra = run_fn(bgra.copy())
        assert out_bgra.shape == (120, 120, 4)
        expected_bgra = MinEnclosing(steps[0].params).compute(bgra.copy())
        assert np.array_equal(out_bgra, expected_bgra)

    def test_exporter_pixel_equivalence_all_geometries(self):
        star = _synthetic_star_image()
        bgr = cv2.cvtColor(star, cv2.COLOR_GRAY2BGR)

        for geom in ("ROTATED_BOX", "ENCLOSING_CIRCLE", "FIT_ELLIPSE", "ALL_SHAPES"):
            params = {
                "geometry": geom,
                "min_area": 40,
                "box_color": "#00ffff",
                "circle_color": "#ff00ff",
                "ellipse_color": "#ffff00",
                "thickness": 2,
                "show_contours": True,
            }
            steps = [PipelineStep(block_id="s1", type="transformation_minenclosing", params=params)]
            script, _ = export_pipeline_to_python(steps)
            scope = {}
            exec(script, scope)
            run_fn = scope["run_pipeline"]
            op = MinEnclosing(params)

            assert np.array_equal(run_fn(bgr.copy()), op.compute(bgr.copy()))

    def test_exporter_does_not_mutate_input_buffer(self):
        star = _synthetic_star_image()
        bgr = cv2.cvtColor(star, cv2.COLOR_GRAY2BGR)
        bgr_clone = bgr.copy()
        steps = [
            PipelineStep(
                block_id="s1",
                type="transformation_minenclosing",
                params={"geometry": "ALL_SHAPES", "min_area": 50},
            )
        ]
        script, _ = export_pipeline_to_python(steps)
        scope = {}
        exec(script, scope)
        run_fn = scope["run_pipeline"]
        run_fn(bgr)
        np.testing.assert_array_equal(bgr, bgr_clone)

    def test_collinear_5_points_contour_fit_ellipse_does_not_crash(self):
        # A 1-pixel thin horizontal line produces collinear contour points
        canvas = np.zeros((64, 64), dtype=np.uint8)
        canvas[32, 10:40] = 255
        op = MinEnclosing({"geometry": "FIT_ELLIPSE", "min_area": 0})
        result = op.compute(canvas)
        assert result.shape == (64, 64)
        assert result.dtype == np.uint8

    def test_degenerate_1_and_2_point_contours_fit_ellipse_does_not_crash(self):
        # Degenerate 1-pixel and 2-pixel contours have len(cnt) < 5 and must safely skip fitEllipse
        canvas = np.zeros((64, 64, 3), dtype=np.uint8)
        canvas[10, 10] = [255, 255, 255]
        canvas[20, 20:22] = [255, 255, 255]
        op = MinEnclosing({"geometry": "FIT_ELLIPSE", "min_area": 0})
        result = op.compute(canvas)
        assert result.shape == (64, 64, 3)
        assert result.dtype == np.uint8

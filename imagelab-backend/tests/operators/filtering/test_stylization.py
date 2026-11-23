import ast

import cv2
import numpy as np
import pytest

from app.models.pipeline import PipelineStep
from app.operators.filtering.stylization import Stylization
from app.services.python_exporter.generator import export_pipeline_to_python


@pytest.fixture
def synthetic_scene() -> np.ndarray:
    """Creates a 120x120 multi-colored synthetic scene with gradients and shapes."""
    img = np.zeros((120, 120, 3), dtype=np.uint8)
    for y in range(120):
        img[y, :, 0] = int(y * 2)
        img[y, :, 1] = int((120 - y) * 2)
        img[y, :, 2] = 120
    cv2.circle(img, (60, 60), 30, (30, 200, 240), -1)
    cv2.rectangle(img, (20, 20), (50, 50), (220, 50, 30), -1)
    cv2.line(img, (10, 110), (110, 10), (255, 255, 255), 3)
    return img


class TestStylization:
    def test_watercolor_mode_color(self, synthetic_scene):
        op = Stylization({"mode": "WATERCOLOR", "sigma_s": 60, "sigma_r": 0.45})
        result = op.compute(synthetic_scene)
        assert result.shape == synthetic_scene.shape
        assert result.dtype == np.uint8
        assert not np.array_equal(result, synthetic_scene)

    def test_pencil_gray_mode_color(self, synthetic_scene):
        op = Stylization(
            {
                "mode": "PENCIL_GRAY",
                "sigma_s": 60,
                "sigma_r": 0.07,
                "shade_factor": 0.05,
            }
        )
        result = op.compute(synthetic_scene)
        assert result.shape == synthetic_scene.shape
        assert result.dtype == np.uint8
        assert not np.array_equal(result, synthetic_scene)

    def test_pencil_color_mode_color(self, synthetic_scene):
        op = Stylization(
            {
                "mode": "PENCIL_COLOR",
                "sigma_s": 60,
                "sigma_r": 0.07,
                "shade_factor": 0.05,
            }
        )
        result = op.compute(synthetic_scene)
        assert result.shape == synthetic_scene.shape
        assert result.dtype == np.uint8
        assert not np.array_equal(result, synthetic_scene)

    def test_detail_enhance_mode_color(self, synthetic_scene):
        op = Stylization({"mode": "DETAIL_ENHANCE", "sigma_s": 10, "sigma_r": 0.15})
        result = op.compute(synthetic_scene)
        assert result.shape == synthetic_scene.shape
        assert result.dtype == np.uint8
        assert not np.array_equal(result, synthetic_scene)

    def test_grayscale_2d_input(self, synthetic_scene):
        gray = cv2.cvtColor(synthetic_scene, cv2.COLOR_BGR2GRAY)

        op_wc = Stylization({"mode": "WATERCOLOR", "sigma_s": 50, "sigma_r": 0.4})
        res_wc = op_wc.compute(gray)
        assert res_wc.ndim == 2
        assert res_wc.shape == gray.shape

        op_pg = Stylization({"mode": "PENCIL_GRAY", "sigma_s": 50, "sigma_r": 0.1})
        res_pg = op_pg.compute(gray)
        assert res_pg.ndim == 2
        assert res_pg.shape == gray.shape

    def test_single_channel_3d_input(self, synthetic_scene):
        gray = cv2.cvtColor(synthetic_scene, cv2.COLOR_BGR2GRAY)[:, :, np.newaxis]
        op = Stylization({"mode": "WATERCOLOR", "sigma_s": 50, "sigma_r": 0.4})
        res = op.compute(gray)
        assert res.shape == (120, 120, 1)

    def test_rgba_preserves_alpha(self, synthetic_scene):
        alpha = np.full((120, 120, 1), 210, dtype=np.uint8)
        rgba = np.dstack([synthetic_scene, alpha])

        op = Stylization({"mode": "WATERCOLOR", "sigma_s": 60, "sigma_r": 0.45})
        res = op.compute(rgba)
        assert res.shape == (120, 120, 4)
        np.testing.assert_array_equal(res[:, :, 3], alpha[:, :, 0])
        assert not np.array_equal(res[:, :, :3], synthetic_scene)

    def test_invalid_inputs(self):
        op = Stylization({})
        with pytest.raises(ValueError):
            op.compute(None)

        with pytest.raises(ValueError):
            op.compute(np.empty((0, 0), dtype=np.uint8))

        with pytest.raises(ValueError):
            op.compute(np.ones((20, 20, 5), dtype=np.uint8))

        with pytest.raises(ValueError):
            op.compute(np.ones((20, 20), dtype=np.float32))

    def test_python_exporter_ast(self):
        step = PipelineStep(
            id="step_stylization",
            type="filtering_stylization",
            params={
                "mode": "PENCIL_COLOR",
                "sigma_s": 80.0,
                "sigma_r": 0.08,
                "shade_factor": 0.04,
            },
        )
        code, _ = export_pipeline_to_python([step])
        parsed = ast.parse(code)
        assert parsed is not None
        assert "cv2.pencilSketch" in code

    def test_non_contiguous_array_input(self, synthetic_scene):
        sliced = synthetic_scene[::2, ::2, :]
        assert not sliced.flags.c_contiguous
        op = Stylization({"mode": "WATERCOLOR", "sigma_s": 50.0, "sigma_r": 0.4})
        res = op.compute(sliced)
        assert res.shape == sliced.shape
        assert res.dtype == np.uint8

    def test_python_exporter_execution_parity(self, synthetic_scene):
        params = {
            "mode": "WATERCOLOR",
            "sigma_s": 60.0,
            "sigma_r": 0.45,
        }
        op = Stylization(params)
        expected = op.compute(synthetic_scene)

        step = PipelineStep(id="s1", type="filtering_stylization", params=params)
        code, _ = export_pipeline_to_python([step])

        scope = {}
        exec(code, scope)
        run_fn = scope["run_pipeline"]
        actual = run_fn(synthetic_scene.copy())

        np.testing.assert_array_equal(actual, expected)

    def test_python_exporter_pencil_gray_parity(self, synthetic_scene):
        params = {
            "mode": "PENCIL_GRAY",
            "sigma_s": 50.0,
            "sigma_r": 0.08,
            "shade_factor": 0.04,
        }
        op = Stylization(params)
        expected = op.compute(synthetic_scene)

        step = PipelineStep(id="s2", type="filtering_stylization", params=params)
        code, _ = export_pipeline_to_python([step])

        scope = {}
        exec(code, scope)
        run_fn = scope["run_pipeline"]
        actual = run_fn(synthetic_scene.copy())

        np.testing.assert_array_equal(actual, expected)

    def test_python_exporter_pencil_color_parity(self, synthetic_scene):
        params = {
            "mode": "PENCIL_COLOR",
            "sigma_s": 55.0,
            "sigma_r": 0.07,
            "shade_factor": 0.05,
        }
        op = Stylization(params)
        expected = op.compute(synthetic_scene)

        step = PipelineStep(id="s3", type="filtering_stylization", params=params)
        code, _ = export_pipeline_to_python([step])

        scope = {}
        exec(code, scope)
        run_fn = scope["run_pipeline"]
        actual = run_fn(synthetic_scene.copy())

        np.testing.assert_array_equal(actual, expected)

    def test_python_exporter_detail_enhance_parity(self, synthetic_scene):
        params = {
            "mode": "DETAIL_ENHANCE",
            "sigma_s": 15.0,
            "sigma_r": 0.2,
        }
        op = Stylization(params)
        expected = op.compute(synthetic_scene)

        step = PipelineStep(id="s4", type="filtering_stylization", params=params)
        code, _ = export_pipeline_to_python([step])

        scope = {}
        exec(code, scope)
        run_fn = scope["run_pipeline"]
        actual = run_fn(synthetic_scene.copy())

        np.testing.assert_array_equal(actual, expected)

    def test_python_exporter_grayscale_parity(self, synthetic_scene):
        gray = cv2.cvtColor(synthetic_scene, cv2.COLOR_BGR2GRAY)
        params = {
            "mode": "PENCIL_GRAY",
            "sigma_s": 40.0,
            "sigma_r": 0.09,
            "shade_factor": 0.03,
        }
        op = Stylization(params)
        expected = op.compute(gray)

        step = PipelineStep(id="s5", type="filtering_stylization", params=params)
        code, _ = export_pipeline_to_python([step])

        scope = {}
        exec(code, scope)
        run_fn = scope["run_pipeline"]
        actual = run_fn(gray.copy())

        np.testing.assert_array_equal(actual, expected)

    def test_python_exporter_bgra_parity(self, synthetic_scene):
        alpha = np.full((120, 120, 1), 220, dtype=np.uint8)
        bgra = np.dstack([synthetic_scene, alpha])
        params = {
            "mode": "WATERCOLOR",
            "sigma_s": 45.0,
            "sigma_r": 0.35,
        }
        op = Stylization(params)
        expected = op.compute(bgra)

        step = PipelineStep(id="s6", type="filtering_stylization", params=params)
        code, _ = export_pipeline_to_python([step])

        scope = {}
        exec(code, scope)
        run_fn = scope["run_pipeline"]
        actual = run_fn(bgra.copy())

        np.testing.assert_array_equal(actual, expected)

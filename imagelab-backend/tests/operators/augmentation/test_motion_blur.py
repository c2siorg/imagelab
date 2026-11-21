import ast

import numpy as np
import pytest

from app.operators.augmentation.motion_blur import MotionBlur
from app.services.python_exporter.generator import export_pipeline_to_python


class TestMotionBlur:
    def test_invalid_inputs_raise_value_error(self):
        op = MotionBlur({})
        with pytest.raises(ValueError, match="invalid or empty image"):
            op.compute(None)

        with pytest.raises(ValueError, match="invalid or empty image"):
            op.compute(np.empty((0, 0), dtype=np.uint8))

        with pytest.raises(ValueError, match="2-D or 3-D image"):
            op.compute(np.zeros((10, 10, 5), dtype=np.uint8))

        with pytest.raises(ValueError, match="uint8 image"):
            op.compute(np.zeros((10, 10), dtype=np.float32))

    def test_horizontal_motion_blur_spreads_horizontally(self):
        # Single bright impulse in the center of a dark image
        img = np.zeros((31, 31), dtype=np.uint8)
        img[15, 15] = 255

        op = MotionBlur({"kernel_size": 11, "angle": 0.0})
        res = op.compute(img)
        assert res.shape == (31, 31)
        assert res.dtype == np.uint8

        # In horizontal motion blur, blurred values spread along row 15
        assert np.all(res[15, 10:21] > 0)
        # Above and below row 15 should remain zero
        assert np.all(res[14, :] == 0)
        assert np.all(res[16, :] == 0)

    def test_vertical_motion_blur_spreads_vertically(self):
        img = np.zeros((31, 31), dtype=np.uint8)
        img[15, 15] = 255

        op = MotionBlur({"kernel_size": 11, "angle": 90.0})
        res = op.compute(img)
        assert res.shape == (31, 31)

        # In vertical motion blur, blurred values spread along col 15
        assert np.all(res[10:21, 15] > 0)
        assert np.all(res[:, 14] == 0)
        assert np.all(res[:, 16] == 0)

    def test_diagonal_motion_blur_spreads_diagonally(self):
        # Center impulse in dark image
        img = np.zeros((31, 31), dtype=np.uint8)
        img[15, 15] = 255

        op = MotionBlur({"kernel_size": 11, "angle": 45.0})
        res = op.compute(img)
        assert res.shape == (31, 31)
        assert res.dtype == np.uint8

        # In 45-degree motion blur, blur energy spreads along the anti-diagonal (x + y ~ 30)
        # Check that diagonal points away from center receive blur energy
        assert res[13, 17] > 0 or res[14, 16] > 0
        assert res[17, 13] > 0 or res[16, 14] > 0
        # Purely orthogonal far points remain zero
        assert res[15, 5] == 0
        assert res[5, 15] == 0

        # Verify kernel normalization preserves energy on uniform input
        uniform = np.full((31, 31), 180, dtype=np.uint8)
        res_uniform = op.compute(uniform)
        # Interior points away from boundary should remain unchanged
        np.testing.assert_array_equal(res_uniform[10:21, 10:21], 180)

    def test_supports_single_channel_3d(self):
        img = np.zeros((20, 20, 1), dtype=np.uint8)
        img[10, 10, 0] = 255
        op = MotionBlur({"kernel_size": 5, "angle": 45.0})
        res = op.compute(img)
        assert res.shape == (20, 20, 1)
        assert res.dtype == np.uint8
        assert res[10, 10, 0] > 0

    def test_supports_bgr_image(self):
        img = np.zeros((31, 31, 3), dtype=np.uint8)
        img[15, 15] = [255, 0, 0]  # pure blue impulse
        op = MotionBlur({"kernel_size": 7, "angle": 0.0})
        res = op.compute(img)
        assert res.shape == (31, 31, 3)
        assert res.dtype == np.uint8
        # Blue channel spreads horizontally
        assert np.all(res[15, 12:19, 0] > 0)
        # Green and red channels remain zero
        assert np.all(res[:, :, 1] == 0)
        assert np.all(res[:, :, 2] == 0)

    def test_preserves_bgra_alpha_channel(self):
        bgra = np.full((25, 25, 4), 100, dtype=np.uint8)
        bgra[:, :, 3] = 210
        op = MotionBlur({"kernel_size": 9, "angle": 60.0})
        res = op.compute(bgra)
        assert res.shape == (25, 25, 4)
        np.testing.assert_array_equal(res[:, :, 3], 210)

    def test_even_kernel_size_promotes_to_odd(self):
        img = np.zeros((25, 25), dtype=np.uint8)
        img[12, 12] = 255
        op_even = MotionBlur({"kernel_size": 10, "angle": 0.0})
        op_odd = MotionBlur({"kernel_size": 11, "angle": 0.0})
        np.testing.assert_array_equal(op_even.compute(img), op_odd.compute(img))

    def test_clamping_kernel_size_bounds(self):
        img = np.zeros((31, 31), dtype=np.uint8)
        img[15, 15] = 255
        # Underflow clamps to min kernel size 3
        op_min = MotionBlur({"kernel_size": -5, "angle": 0.0})
        res_min = op_min.compute(img)
        # Kernel size 3 spreads only 1 pixel in each direction
        assert res_min[15, 14] > 0
        assert res_min[15, 16] > 0
        assert res_min[15, 13] == 0
        assert res_min[15, 17] == 0

        # Overflow clamps to 61
        op_max = MotionBlur({"kernel_size": 500, "angle": 0.0})
        res_max = op_max.compute(img)
        assert res_max.shape == (31, 31)
        assert np.all(res_max[15, :] > 0)


class TestMotionBlurExporter:
    def test_export_script_compiles_and_matches_operator_parity(self):
        pipeline = [
            {
                "type": "augmentation_motionblur",
                "params": {"kernel_size": 9, "angle": 45.0},
            }
        ]
        script, _ = export_pipeline_to_python(pipeline)
        tree = ast.parse(script)
        assert tree is not None

        code_obj = compile(tree, filename="<test_mb_export>", mode="exec")
        scope = {}
        exec(code_obj, scope)
        assert "run_pipeline" in scope

        img = np.zeros((30, 30, 3), dtype=np.uint8)
        img[15, 15] = [200, 150, 100]
        out = scope["run_pipeline"](img.copy())
        assert out.shape == (30, 30, 3)
        assert out.dtype == np.uint8

        expected = MotionBlur(pipeline[0]["params"]).compute(img.copy())
        np.testing.assert_array_equal(out, expected)

    def test_chained_motion_blur_blocks_do_not_collide(self):
        # Two consecutive motion blur blocks with different parameters
        pipeline = [
            {"type": "augmentation_motionblur", "params": {"kernel_size": 5, "angle": 0.0}},
            {"type": "augmentation_motionblur", "params": {"kernel_size": 7, "angle": 90.0}},
        ]
        script, _ = export_pipeline_to_python(pipeline)
        tree = ast.parse(script)
        assert tree is not None

        code_obj = compile(tree, filename="<test_mb_chained>", mode="exec")
        scope = {}
        exec(code_obj, scope)
        img = np.zeros((25, 25, 3), dtype=np.uint8)
        img[12, 12] = [255, 255, 255]
        out = scope["run_pipeline"](img.copy())
        assert out.shape == (25, 25, 3)

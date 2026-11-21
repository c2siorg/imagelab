import ast

import cv2
import numpy as np
import pytest

from app.operators.filtering.unsharp_mask import UnsharpMask
from app.services.python_exporter.generator import export_pipeline_to_python


class TestUnsharpMask:
    def test_invalid_inputs_raise_value_error(self):
        op = UnsharpMask({})
        with pytest.raises(ValueError, match="invalid or empty image"):
            op.compute(None)

        with pytest.raises(ValueError, match="invalid or empty image"):
            op.compute(np.empty((0, 0), dtype=np.uint8))

        with pytest.raises(ValueError, match="2-D or 3-D image"):
            op.compute(np.zeros((10, 10, 5), dtype=np.uint8))

        with pytest.raises(ValueError, match="uint8 image"):
            op.compute(np.zeros((10, 10), dtype=np.float32))

    def test_sharpens_soft_edges(self):
        # Create a synthetic image with a blurred edge
        img = np.zeros((50, 50), dtype=np.uint8)
        img[:, 25:] = 200
        soft = cv2.GaussianBlur(img, (5, 5), 1.0)

        op = UnsharpMask({"kernel_size": 5, "sigma": 1.0, "amount": 2.0, "threshold": 0})
        res = op.compute(soft)
        assert res.shape == (50, 50)
        assert res.dtype == np.uint8

        # Unsharp mask accentuates edge overshoot and undershoot (acutance)
        # Pixel right before the edge should be darker than or equal to soft
        # Pixel right after the edge should be brighter than or equal to soft
        assert res[25, 26] >= soft[25, 26]
        assert res[25, 24] <= soft[25, 24]

    def test_threshold_gate_suppresses_subtle_variations(self):
        img = np.full((30, 30), 100, dtype=np.uint8)
        # Subtle variance of 2 intensity levels
        img[15, 15] = 102

        # With threshold = 5, difference < 5 is gated out to 0
        op_thresh = UnsharpMask({"threshold": 5, "amount": 2.0})
        res_thresh = op_thresh.compute(img)
        np.testing.assert_array_equal(res_thresh, img)

        # Without threshold, difference is sharpened
        op_no_thresh = UnsharpMask({"threshold": 0, "amount": 2.0})
        res_no_thresh = op_no_thresh.compute(img)
        assert not np.array_equal(res_no_thresh, img)

    def test_supports_single_channel_3d(self):
        img = np.full((20, 20, 1), 100, dtype=np.uint8)
        img[10, 10, 0] = 200
        op = UnsharpMask({"kernel_size": 3, "amount": 1.5})
        res = op.compute(img)
        assert res.shape == (20, 20, 1)
        assert res.dtype == np.uint8

    def test_supports_bgr_image(self):
        img = np.full((25, 25, 3), 100, dtype=np.uint8)
        img[12, 12] = [200, 50, 150]
        op = UnsharpMask({"kernel_size": 5, "amount": 1.5})
        res = op.compute(img)
        assert res.shape == (25, 25, 3)
        assert res.dtype == np.uint8

    def test_preserves_bgra_alpha_channel(self):
        bgra = np.full((25, 25, 4), 100, dtype=np.uint8)
        bgra[:, :, 3] = 175
        bgra[12, 12, :3] = [220, 30, 180]
        op = UnsharpMask({"kernel_size": 5, "amount": 1.5})
        res = op.compute(bgra)
        assert res.shape == (25, 25, 4)
        np.testing.assert_array_equal(res[:, :, 3], 175)

    def test_even_kernel_size_promotes_to_odd(self):
        img = np.zeros((25, 25), dtype=np.uint8)
        img[12, 12] = 255
        op_even = UnsharpMask({"kernel_size": 6})
        op_odd = UnsharpMask({"kernel_size": 7})
        np.testing.assert_array_equal(op_even.compute(img), op_odd.compute(img))

    def test_clamping_parameter_bounds(self):
        img = np.zeros((15, 15), dtype=np.uint8)
        op = UnsharpMask(
            {
                "kernel_size": 100,
                "sigma": 50.0,
                "amount": 10.0,
                "threshold": 100,
            }
        )
        res = op.compute(img)
        assert res.shape == (15, 15)


class TestUnsharpMaskExporter:
    def test_export_script_compiles_and_runs(self):
        pipeline = [
            {
                "type": "filtering_unsharpmask",
                "params": {
                    "kernel_size": 5,
                    "sigma": 1.2,
                    "amount": 2.0,
                    "threshold": 2,
                },
            }
        ]
        script, _ = export_pipeline_to_python(pipeline)
        tree = ast.parse(script)
        assert tree is not None

        code_obj = compile(tree, filename="<test_unsharp_export>", mode="exec")
        scope = {}
        exec(code_obj, scope)
        assert "run_pipeline" in scope

        img = np.zeros((30, 30, 3), dtype=np.uint8)
        img[15, 15] = [200, 200, 200]
        out = scope["run_pipeline"](img)
        assert out.shape == (30, 30, 3)
        assert out.dtype == np.uint8

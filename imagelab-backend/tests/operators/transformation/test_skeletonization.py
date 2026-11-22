import ast

import cv2
import numpy as np
import pytest

from app.models.pipeline import PipelineStep
from app.operators.transformation.skeletonization import Skeletonization
from app.services.python_exporter.generator import export_pipeline_to_python


def _synthetic_shapes_image() -> np.ndarray:
    """Creates a 100x100 synthetic binary image with thick lines and geometric shapes."""
    img = np.zeros((100, 100), dtype=np.uint8)
    # Thick circle ring
    cv2.circle(img, (50, 50), 30, 255, thickness=12)
    # Thick diagonal bar
    cv2.line(img, (15, 15), (85, 85), 255, thickness=10)
    # Filled central cross
    cv2.rectangle(img, (45, 20), (55, 80), 255, -1)
    cv2.rectangle(img, (20, 45), (80, 55), 255, -1)
    return img


class TestSkeletonization:
    def test_thinning_reduces_pixel_count(self):
        img = _synthetic_shapes_image()
        orig_count = cv2.countNonZero(img)

        op = Skeletonization(
            {
                "element": "CROSS",
                "kernel_size": 3,
                "threshold": 127,
                "max_iterations": 0,
                "output_mode": "BINARY_MASK",
            }
        )
        result = op.compute(img)
        assert result.shape == (100, 100)
        assert result.dtype == np.uint8

        skel_count = cv2.countNonZero(result)
        assert skel_count > 0
        # Morphological skeleton must significantly thin the thick 10-12px shapes
        assert skel_count < orig_count * 0.35

    def test_structuring_elements(self):
        img = _synthetic_shapes_image()
        for elem in ("CROSS", "RECTANGLE", "ELLIPSE"):
            op = Skeletonization(
                {
                    "element": elem,
                    "kernel_size": 3,
                    "threshold": 127,
                    "max_iterations": 0,
                    "output_mode": "BINARY_MASK",
                }
            )
            result = op.compute(img)
            assert result.shape == (100, 100)
            assert cv2.countNonZero(result) > 0

    def test_max_iterations_bounding(self):
        img = _synthetic_shapes_image()
        op_partial = Skeletonization({"max_iterations": 3, "output_mode": "BINARY_MASK"})
        op_full = Skeletonization({"max_iterations": 0, "output_mode": "BINARY_MASK"})

        res_partial = op_partial.compute(img)
        res_full = op_full.compute(img)

        count_partial = cv2.countNonZero(res_partial)
        count_full = cv2.countNonZero(res_full)

        # In morphological skeletonization, each iteration unions additional skeletal subsets:
        # early stopping bounds accumulated skeleton points.
        assert count_partial <= count_full
        assert count_full > 0

    def test_invert_mode(self):
        # Create dark shape on bright white background
        white_bg = np.full((80, 80), 255, dtype=np.uint8)
        cv2.circle(white_bg, (40, 40), 20, 0, thickness=8)

        op = Skeletonization({"invert": True, "output_mode": "BINARY_MASK"})
        result = op.compute(white_bg)
        assert cv2.countNonZero(result) > 0
        # The center should contain skeleton pixels of the circular ring
        assert result.shape == (80, 80)

    def test_overlay_mode(self):
        img = _synthetic_shapes_image()
        bgr = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

        op = Skeletonization(
            {
                "output_mode": "OVERLAY",
                "skeleton_color": "#00ffff",  # Cyan in BGR is (255, 255, 0)
            }
        )
        result = op.compute(bgr)
        assert result.shape == (100, 100, 3)
        assert result.dtype == np.uint8

        # Cyan pixels should exist where skeleton was drawn
        cyan_mask = (result[:, :, 0] == 255) & (result[:, :, 1] == 255) & (result[:, :, 2] == 0)
        assert np.any(cyan_mask)

    def test_overlay_mode_grayscale(self):
        img = _synthetic_shapes_image()
        op = Skeletonization(
            {
                "output_mode": "OVERLAY",
                "skeleton_color": "#ffffff",
            }
        )
        result = op.compute(img)
        assert result.ndim == 2
        assert result.shape == (100, 100)

    def test_channel_preservation_binary_mask(self):
        img = _synthetic_shapes_image()

        # 2D Grayscale -> 2D
        op = Skeletonization({"output_mode": "BINARY_MASK"})
        res_2d = op.compute(img)
        assert res_2d.ndim == 2

        # 3D 1-channel -> (H, W, 1)
        img_1ch = img[:, :, np.newaxis]
        res_1ch = op.compute(img_1ch)
        assert res_1ch.shape == (100, 100, 1)

        # 3-channel BGR -> (H, W, 3)
        bgr = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        res_bgr = op.compute(bgr)
        assert res_bgr.shape == (100, 100, 3)

        # 4-channel BGRA -> (H, W, 4) with background alpha preserved and skeleton made opaque
        alpha = np.full((100, 100, 1), 180, dtype=np.uint8)
        bgra = np.dstack((bgr, alpha))
        res_bgra = op.compute(bgra)
        assert res_bgra.shape == (100, 100, 4)
        skel_mask = res_bgra[:, :, 0] > 0
        assert np.all(res_bgra[skel_mask, 3] == 255)
        assert np.all(res_bgra[~skel_mask, 3] == 180)

    def test_invalid_inputs(self):
        op = Skeletonization({})
        with pytest.raises(ValueError):
            op.compute(None)

        with pytest.raises(ValueError):
            op.compute(np.empty((0, 0), dtype=np.uint8))

        with pytest.raises(ValueError):
            op.compute(np.ones((10, 10, 5), dtype=np.uint8))

        with pytest.raises(ValueError):
            op.compute(np.ones((10, 10), dtype=np.float32))

    def test_all_black_image_early_exit(self):
        black = np.zeros((80, 80), dtype=np.uint8)
        op = Skeletonization({"threshold": 127, "output_mode": "BINARY_MASK"})
        result = op.compute(black)
        assert result.shape == (80, 80)
        assert cv2.countNonZero(result) == 0

    def test_all_white_image_safe_bounding(self):
        white = np.full((60, 60), 255, dtype=np.uint8)
        op = Skeletonization({"threshold": 127, "max_iterations": 5, "output_mode": "BINARY_MASK"})
        result = op.compute(white)
        assert result.shape == (60, 60)
        assert result.dtype == np.uint8

    def test_alpha_channel_visibility(self):
        img = _synthetic_shapes_image()
        bgr = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        # Transparent background (alpha=0)
        alpha = np.zeros((100, 100, 1), dtype=np.uint8)
        bgra = np.dstack((bgr, alpha))

        op = Skeletonization({"output_mode": "BINARY_MASK"})
        res = op.compute(bgra)
        assert res.shape == (100, 100, 4)
        # Skeleton pixels must have alpha = 255
        skel_mask = res[:, :, 0] > 0
        assert np.any(skel_mask)
        assert np.all(res[skel_mask, 3] == 255)

    def test_python_exporter_ast(self):
        step = PipelineStep(
            id="step_1",
            type="transformation_skeletonization",
            params={
                "element": "ELLIPSE",
                "kernel_size": 3,
                "threshold": 120,
                "invert": False,
                "max_iterations": 50,
                "output_mode": "OVERLAY",
                "skeleton_color": "#00ffff",
            },
        )
        code, _ = export_pipeline_to_python([step])
        # Verify valid Python syntax
        parsed = ast.parse(code)
        assert parsed is not None
        assert "cv2.MORPH_ELLIPSE" in code
        assert "while True:" in code

    def test_python_exporter_execution_parity(self):
        img = _synthetic_shapes_image()
        bgr = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

        params = {
            "element": "CROSS",
            "kernel_size": 3,
            "threshold": 127,
            "invert": False,
            "max_iterations": 0,
            "output_mode": "BINARY_MASK",
        }

        # Direct compute
        op = Skeletonization(params)
        expected = op.compute(bgr)

        # Exporter execution
        step = PipelineStep(id="s1", type="transformation_skeletonization", params=params)
        code, _ = export_pipeline_to_python([step])

        scope = {}
        exec(code, scope)
        run_fn = scope["run_pipeline"]
        actual = run_fn(bgr.copy())

        assert np.array_equal(actual, expected)

    def test_python_exporter_overlay_parity(self):
        img = _synthetic_shapes_image()
        bgr = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

        params = {
            "element": "RECTANGLE",
            "kernel_size": 3,
            "threshold": 127,
            "invert": False,
            "max_iterations": 10,
            "output_mode": "OVERLAY",
            "skeleton_color": "#ff00ff",
        }

        op = Skeletonization(params)
        expected = op.compute(bgr)

        step = PipelineStep(id="s2", type="transformation_skeletonization", params=params)
        code, _ = export_pipeline_to_python([step])

        scope = {}
        exec(code, scope)
        run_fn = scope["run_pipeline"]
        actual = run_fn(bgr.copy())

        assert np.array_equal(actual, expected)

    def test_python_exporter_grayscale_parity(self):
        img = _synthetic_shapes_image()

        params = {
            "element": "ELLIPSE",
            "kernel_size": 3,
            "threshold": 127,
            "invert": False,
            "max_iterations": 0,
            "output_mode": "OVERLAY",
            "skeleton_color": "#ffffff",
        }

        op = Skeletonization(params)
        expected = op.compute(img)

        step = PipelineStep(id="s3", type="transformation_skeletonization", params=params)
        code, _ = export_pipeline_to_python([step])

        scope = {}
        exec(code, scope)
        run_fn = scope["run_pipeline"]
        actual = run_fn(img.copy())

        assert np.array_equal(actual, expected)

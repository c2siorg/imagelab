import ast

import cv2
import numpy as np
import pytest

from app.models.pipeline import PipelineStep
from app.operators.geometric.perspective_transform import (
    PerspectiveTransform,
    _has_collinear_triplet,
)
from app.services.python_exporter.generator import export_pipeline_to_python


def _make_test_image(channels: int = 3) -> np.ndarray:
    """Generate a 200x200 image with distinct geometric patterns."""
    if channels == 1:
        img = np.zeros((200, 200), dtype=np.uint8)
        cv2.rectangle(img, (40, 40), (160, 160), 200, -1)
        cv2.circle(img, (100, 100), 30, 100, -1)
        return img

    img = np.zeros((200, 200, channels), dtype=np.uint8)
    img[:, :, 0] = 50
    if channels >= 3:
        img[:, :, 1] = 100
        img[:, :, 2] = 150
        cv2.rectangle(img, (40, 40), (160, 160), (255, 255, 255) if channels == 3 else (255, 255, 255, 255), -1)
        cv2.circle(img, (100, 100), 30, (0, 0, 255) if channels == 3 else (0, 0, 255, 255), -1)
    if channels == 4:
        img[:, :, 3] = 180  # semi-transparent
    return img


class TestPerspectiveTransform:
    def test_identity_default_mapping(self):
        img = _make_test_image(3)
        res = PerspectiveTransform({}).compute(img)
        assert res.shape == (200, 200, 3)
        # Default mapping maps all 4 corners to themselves, yielding identity
        assert np.array_equal(res, img)

    def test_quadrilateral_warp(self):
        img = _make_test_image(3)
        # Warp full rectangle to trapezoid
        params = {
            "src_x1": 0,
            "src_y1": 0,
            "src_x2": 199,
            "src_y2": 0,
            "src_x3": 199,
            "src_y3": 199,
            "src_x4": 0,
            "src_y4": 199,
            "dst_x1": 30,
            "dst_y1": 20,
            "dst_x2": 170,
            "dst_y2": 20,
            "dst_x3": 199,
            "dst_y3": 199,
            "dst_x4": 0,
            "dst_y4": 199,
        }
        res = PerspectiveTransform(params).compute(img)
        assert res.shape == (200, 200, 3)
        assert not np.array_equal(res, img)
        # Outside the warped trapezoid should be black border (0, 0, 0)
        assert np.array_equal(res[0, 0], [0, 0, 0])

    def test_custom_output_dimensions(self):
        img = _make_test_image(3)
        params = {
            "output_width": 320,
            "output_height": 240,
        }
        res = PerspectiveTransform(params).compute(img)
        assert res.shape == (240, 320, 3)

    def test_grayscale_2d_and_3d_single_channel(self):
        gray2d = _make_test_image(1)
        res2d = PerspectiveTransform({}).compute(gray2d)
        assert res2d.shape == (200, 200)
        assert res2d.ndim == 2

        gray3d = gray2d[:, :, np.newaxis]
        res3d = PerspectiveTransform({}).compute(gray3d)
        assert res3d.shape == (200, 200, 1)

    def test_bgra_4_channel_preserves_channels(self):
        bgra = _make_test_image(4)
        res = PerspectiveTransform({}).compute(bgra)
        assert res.shape == (200, 200, 4)
        assert np.array_equal(res, bgra)

    def test_collinear_source_points_returns_unmodified(self):
        img = _make_test_image(3)
        # Top 3 points lie on the same horizontal line (y = 0)
        params = {
            "src_x1": 0,
            "src_y1": 0,
            "src_x2": 50,
            "src_y2": 0,
            "src_x3": 100,
            "src_y3": 0,
            "src_x4": 0,
            "src_y4": 100,
        }
        res = PerspectiveTransform(params).compute(img)
        assert np.array_equal(res, img)

    def test_collinear_destination_points_returns_unmodified(self):
        img = _make_test_image(3)
        params = {
            "dst_x1": 10,
            "dst_y1": 10,
            "dst_x2": 50,
            "dst_y2": 50,
            "dst_x3": 90,
            "dst_y3": 90,
            "dst_x4": 0,
            "dst_y4": 100,
        }
        res = PerspectiveTransform(params).compute(img)
        assert np.array_equal(res, img)

    def test_collinear_helper(self):
        good = np.float32([(0, 0), (100, 0), (100, 100), (0, 100)])
        assert not _has_collinear_triplet(good)

        bad = np.float32([(0, 0), (50, 0), (100, 0), (0, 100)])
        assert _has_collinear_triplet(bad)

    def test_tiny_image_boundary(self):
        tiny = np.zeros((1, 1, 3), dtype=np.uint8)
        res = PerspectiveTransform({}).compute(tiny)
        assert np.array_equal(res, tiny)

    def test_invalid_empty_image_raises_error(self):
        with pytest.raises(ValueError, match="invalid or empty image"):
            PerspectiveTransform({}).compute(np.array([], dtype=np.uint8))

    def test_invalid_none_image_raises_error(self):
        with pytest.raises(ValueError, match="invalid or empty image"):
            PerspectiveTransform({}).compute(None)

    def test_invalid_dimensions_raises_error(self):
        with pytest.raises(ValueError, match="expects a 2-D or 3-D image"):
            PerspectiveTransform({}).compute(np.zeros((10, 10, 2, 2), dtype=np.uint8))

    def test_python_exporter_perspective_transform(self):
        params = {
            "src_x1": 0,
            "src_y1": 0,
            "src_x2": 199,
            "src_y2": 0,
            "src_x3": 199,
            "src_y3": 199,
            "src_x4": 0,
            "src_y4": 199,
            "dst_x1": 20,
            "dst_y1": 10,
            "dst_x2": 180,
            "dst_y2": 10,
            "dst_x3": 199,
            "dst_y3": 199,
            "dst_x4": 0,
            "dst_y4": 199,
            "output_width": 250,
            "output_height": 220,
        }
        steps = [PipelineStep(type="geometric_perspectivetransform", params=params)]
        code, unsupported = export_pipeline_to_python(steps, "input.png", "output.png")
        assert unsupported == []
        assert "cv2.getPerspectiveTransform" in code
        assert "cv2.warpPerspective" in code

        # 1. AST syntax parsing
        tree = ast.parse(code)
        assert isinstance(tree, ast.Module)

        # 2. Execution on BGR
        compiled = compile(code, "<string>", "exec")
        namespace = {}
        exec(compiled, namespace)
        assert "run_pipeline" in namespace
        run_fn = namespace["run_pipeline"]

        img = _make_test_image(3)
        res = run_fn(img.copy())
        assert res.shape == (220, 250, 3)

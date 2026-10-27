import ast

import numpy as np
import pytest

from app.models.pipeline import PipelineStep
from app.operators.detection.corner_detection import CornerDetection
from app.services.python_exporter.generator import export_pipeline_to_python


def _synthetic_corners_image() -> np.ndarray:
    """Creates a 100x100 BGR image with a solid centered square having 4 sharp corners."""
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    img[25:75, 25:75] = 255
    return img


class TestCornerDetection:
    def test_shi_tomasi_detects_corners(self):
        img = _synthetic_corners_image()
        result = CornerDetection({"method": "SHI_TOMASI", "maxCorners": 20, "rgbcolors_input": "#ff0000"}).compute(img)
        assert result.shape == (100, 100, 3)
        assert result.dtype == np.uint8
        # Since red markers are drawn at corners, red channel will have pixels with [0, 0, 255]
        assert np.any((result[:, :, 2] == 255) & (result[:, :, 0] == 0))

    def test_harris_detects_corners(self):
        img = _synthetic_corners_image()
        result = CornerDetection({"method": "HARRIS", "maxCorners": 20, "rgbcolors_input": "#00ff00"}).compute(img)
        assert result.shape == (100, 100, 3)
        assert result.dtype == np.uint8
        # Green markers drawn
        assert np.any((result[:, :, 1] == 255) & (result[:, :, 0] == 0))

    def test_grayscale_input_converts_to_bgr(self):
        gray = np.zeros((100, 100), dtype=np.uint8)
        gray[25:75, 25:75] = 255
        result = CornerDetection({"method": "SHI_TOMASI"}).compute(gray)
        assert result.shape == (100, 100, 3)
        assert result.dtype == np.uint8

    def test_single_channel_3d_input(self):
        gray_1ch = np.zeros((100, 100, 1), dtype=np.uint8)
        gray_1ch[25:75, 25:75, 0] = 255
        result = CornerDetection({"method": "SHI_TOMASI"}).compute(gray_1ch)
        assert result.shape == (100, 100, 3)
        assert result.dtype == np.uint8

    def test_bgra_input_preserves_alpha_channel(self):
        bgra = np.zeros((100, 100, 4), dtype=np.uint8)
        bgra[:, :, 3] = 120  # semi-transparent background
        bgra[25:75, 25:75, :3] = 255  # white square
        result = CornerDetection({"method": "SHI_TOMASI", "rgbcolors_input": "#ff0000"}).compute(bgra)
        assert result.shape == (100, 100, 4)
        assert result.dtype == np.uint8
        # Background pixels retain original alpha
        assert result[0, 0, 3] == 120
        # Marker pixels are fully opaque (alpha 255)
        assert np.any(result[:, :, 3] == 255)

    def test_max_corners_limit(self):
        img = _synthetic_corners_image()
        # Should execute cleanly with maxCorners = 2
        result = CornerDetection({"maxCorners": 2}).compute(img)
        assert result.shape == (100, 100, 3)

    def test_parameter_clamping_and_tolerances(self):
        img = _synthetic_corners_image()
        # Extreme parameter values must clamp safely without exceptions
        result = CornerDetection(
            {
                "maxCorners": 50000,
                "qualityLevel": 10.0,
                "minDistance": -5,
                "blockSize": 50,
                "k": 1.5,
                "radius": 100,
            }
        ).compute(img)
        assert result.shape == (100, 100, 3)
        assert result.dtype == np.uint8

    def test_invalid_empty_image_raises_error(self):
        with pytest.raises(ValueError, match="invalid or empty image"):
            CornerDetection({}).compute(np.array([], dtype=np.uint8))

    def test_invalid_none_image_raises_error(self):
        with pytest.raises(ValueError, match="invalid or empty image"):
            CornerDetection({}).compute(None)

    def test_invalid_dtype_raises_error(self):
        with pytest.raises(ValueError, match="expects a uint8 image"):
            CornerDetection({}).compute(np.zeros((50, 50), dtype=np.float32))

    def test_invalid_channels_raises_error(self):
        with pytest.raises(ValueError, match="expects a 2-D or 3-D image with 1, 3, or 4 channels"):
            CornerDetection({}).compute(np.zeros((50, 50, 2), dtype=np.uint8))

    def test_python_exporter_corner_detection(self):
        steps = [
            PipelineStep(
                type="detection_cornerdetection",
                params={"method": "SHI_TOMASI", "maxCorners": 30, "radius": 5, "rgbcolors_input": "#ff0000"},
            )
        ]
        code, unsupported = export_pipeline_to_python(steps, "input.png", "output.png")
        assert unsupported == []
        assert "goodFeaturesToTrack" in code
        assert "cv2.circle" in code

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
        bgr_img = _synthetic_corners_image()
        res_bgr = run_fn(bgr_img.copy())
        assert res_bgr.shape == (100, 100, 3)
        assert res_bgr.dtype == np.uint8

        # 4. Test execution on 2-D grayscale image
        gray_img = np.zeros((100, 100), dtype=np.uint8)
        gray_img[25:75, 25:75] = 255
        res_gray = run_fn(gray_img.copy())
        assert res_gray.shape == (100, 100, 3)
        assert res_gray.dtype == np.uint8

        # 5. Test execution on 4-channel BGRA image: alpha channel preserved and markers opaque
        bgra_img = np.zeros((100, 100, 4), dtype=np.uint8)
        bgra_img[:, :, 3] = 120
        bgra_img[25:75, 25:75, :3] = 255
        res_bgra = run_fn(bgra_img.copy())
        assert res_bgra.shape == (100, 100, 4)
        assert res_bgra[0, 0, 3] == 120
        assert np.any(res_bgra[:, :, 3] == 255)

    def test_python_exporter_harris_mode(self):
        steps = [
            PipelineStep(
                type="detection_cornerdetection",
                params={"method": "HARRIS", "maxCorners": 10, "k": 0.05, "rgbcolors_input": "#00ff00"},
            )
        ]
        code, unsupported = export_pipeline_to_python(steps, "input.png", "output.png")
        assert unsupported == []
        assert "useHarrisDetector=True" in code

        compiled = compile(code, "<string>", "exec")
        namespace = {}
        exec(compiled, namespace)
        bgr_img = _synthetic_corners_image()
        res = namespace["run_pipeline"](bgr_img.copy())
        assert res.shape == (100, 100, 3)

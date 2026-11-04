import ast

import cv2
import numpy as np
import pytest

from app.models.pipeline import PipelineStep
from app.operators.detection.orb_detection import OrbDetection
from app.services.python_exporter.generator import export_pipeline_to_python


def _synthetic_textured_image() -> np.ndarray:
    """Creates a 300x300 BGR image with distinct geometric shapes and high-contrast features."""
    img = np.zeros((300, 300, 3), dtype=np.uint8)
    cv2.rectangle(img, (50, 50), (250, 250), (255, 255, 255), 2)
    for i in range(70, 230, 20):
        cv2.circle(img, (i, i), 8, (255, 255, 255), -1)
        cv2.rectangle(img, (i, 250 - i), (i + 10, 260 - i), (200, 200, 200), -1)
    return img


class TestOrbDetection:
    def test_orb_detects_features(self):
        img = _synthetic_textured_image()
        result = OrbDetection({"nfeatures": 50, "color": "#00ff00", "drawRichKeypoints": True}).compute(img)
        assert result.shape == (300, 300, 3)
        assert result.dtype == np.uint8
        # Green markers drawn: green channel higher than red/blue
        assert np.any((result[:, :, 1] > 150) & (result[:, :, 0] < 50))

    def test_score_types(self):
        img = _synthetic_textured_image()
        res_harris = OrbDetection({"scoreType": "HARRIS_SCORE", "nfeatures": 30}).compute(img)
        res_fast = OrbDetection({"scoreType": "FAST_SCORE", "nfeatures": 30}).compute(img)
        assert res_harris.shape == (300, 300, 3)
        assert res_fast.shape == (300, 300, 3)

    def test_draw_rich_keypoints_toggle(self):
        img = _synthetic_textured_image()
        res_rich = OrbDetection({"drawRichKeypoints": True, "nfeatures": 25}).compute(img)
        res_default = OrbDetection({"drawRichKeypoints": False, "nfeatures": 25}).compute(img)
        assert res_rich.shape == (300, 300, 3)
        assert res_default.shape == (300, 300, 3)
        # Visual markers differ between rich and simple point representations
        assert not np.array_equal(res_rich, res_default)

    def test_grayscale_input_converts_to_bgr(self):
        img = _synthetic_textured_image()
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        result = OrbDetection({"color": "#00ff00"}).compute(gray)
        assert result.shape == (300, 300, 3)
        assert result.dtype == np.uint8
        assert np.any(result[:, :, 1] > 150)

    def test_single_channel_3d_input(self):
        img = _synthetic_textured_image()
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)[:, :, np.newaxis]
        result = OrbDetection({"color": "#00ff00"}).compute(gray)
        assert result.shape == (300, 300, 3)
        assert result.dtype == np.uint8

    def test_bgra_input_preserves_alpha_channel(self):
        img = _synthetic_textured_image()
        bgra = np.zeros((300, 300, 4), dtype=np.uint8)
        bgra[:, :, :3] = img
        bgra[:, :, 3] = 135  # semi-transparent background

        result = OrbDetection({"color": "#00ff00"}).compute(bgra)
        assert result.shape == (300, 300, 4)
        assert result.dtype == np.uint8
        # Background pixels maintain original alpha
        assert result[0, 0, 3] == 135
        # Marker pixels have opaque alpha (255)
        assert np.any(result[:, :, 3] == 255)

    def test_empty_feature_image_returns_canvas_safely(self):
        # A completely solid black image has 0 keypoints
        blank = np.zeros((100, 100, 3), dtype=np.uint8)
        result = OrbDetection({"nfeatures": 50}).compute(blank)
        assert result.shape == (100, 100, 3)
        assert np.array_equal(result, blank)

    def test_parameter_clamping_and_tolerances(self):
        img = _synthetic_textured_image()
        # Extreme parameter boundaries must clamp cleanly without throwing
        result = OrbDetection(
            {
                "nfeatures": 99999,
                "scaleFactor": 15.0,
                "nlevels": 99,
                "edgeThreshold": 500,
                "fastThreshold": -10,
            }
        ).compute(img)
        assert result.shape == (300, 300, 3)

    def test_non_uint8_dtype_raises_error(self):
        img = _synthetic_textured_image()
        float_img = img.astype(np.float32) / 255.0
        with pytest.raises(ValueError, match="expects a uint8 image"):
            OrbDetection({"nfeatures": 20}).compute(float_img)

        uint16_img = (img.astype(np.uint16)) * 256
        with pytest.raises(ValueError, match="expects a uint8 image"):
            OrbDetection({"nfeatures": 20}).compute(uint16_img)

    def test_invalid_empty_image_raises_error(self):
        with pytest.raises(ValueError, match="invalid or empty image"):
            OrbDetection({}).compute(np.array([], dtype=np.uint8))

    def test_invalid_none_image_raises_error(self):
        with pytest.raises(ValueError, match="invalid or empty image"):
            OrbDetection({}).compute(None)

    def test_invalid_channels_raises_error(self):
        with pytest.raises(ValueError, match="expects a 2-D or 3-D image with 1, 3, or 4 channels"):
            OrbDetection({}).compute(np.zeros((50, 50, 2), dtype=np.uint8))

    def test_python_exporter_orb_detection(self):
        steps = [
            PipelineStep(
                type="detection_orb",
                params={
                    "nfeatures": 50,
                    "scaleFactor": 1.2,
                    "nlevels": 4,
                    "scoreType": "HARRIS_SCORE",
                    "drawRichKeypoints": True,
                    "color": "#00ff00",
                },
            )
        ]
        code, unsupported = export_pipeline_to_python(steps, "input.png", "output.png")
        assert unsupported == []
        assert "cv2.ORB_create" in code
        assert "cv2.drawKeypoints" in code
        assert "DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS" in code

        # 1. AST syntax parsing
        tree = ast.parse(code)
        assert isinstance(tree, ast.Module)

        # 2. Execution on BGR
        compiled = compile(code, "<string>", "exec")
        namespace = {}
        exec(compiled, namespace)
        assert "run_pipeline" in namespace
        run_fn = namespace["run_pipeline"]

        bgr_img = _synthetic_textured_image()
        res_bgr = run_fn(bgr_img.copy())
        assert res_bgr.shape == (300, 300, 3)
        assert res_bgr.dtype == np.uint8

        # 3. Execution on Grayscale
        gray_img = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2GRAY)
        res_gray = run_fn(gray_img.copy())
        assert res_gray.shape == (300, 300, 3)
        assert res_gray.dtype == np.uint8

        # 4. Execution on BGRA (preserves alpha)
        bgra_img = np.zeros((300, 300, 4), dtype=np.uint8)
        bgra_img[:, :, :3] = bgr_img
        bgra_img[:, :, 3] = 125
        res_bgra = run_fn(bgra_img.copy())
        assert res_bgra.shape == (300, 300, 4)
        assert res_bgra[0, 0, 3] == 125
        assert np.any(res_bgra[:, :, 3] == 255)

    def test_python_exporter_fast_score_mode(self):
        steps = [
            PipelineStep(
                type="detection_orb",
                params={
                    "scoreType": "FAST_SCORE",
                    "drawRichKeypoints": False,
                },
            )
        ]
        code, unsupported = export_pipeline_to_python(steps, "input.png", "output.png")
        assert unsupported == []
        assert "ORB_FAST_SCORE" in code
        assert "DRAW_MATCHES_FLAGS_DEFAULT" in code

        compiled = compile(code, "<string>", "exec")
        namespace = {}
        exec(compiled, namespace)
        bgr_img = _synthetic_textured_image()
        res = namespace["run_pipeline"](bgr_img.copy())
        assert res.shape == (300, 300, 3)

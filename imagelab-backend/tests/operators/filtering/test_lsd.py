import cv2
import numpy as np
import pytest

from app.operators.filtering.lsd import LineSegmentDetector
from app.services.python_exporter.generator import PipelineStep, export_pipeline_to_python


def _run_exported_pipeline(code: str, image: np.ndarray) -> np.ndarray:
    namespace: dict = {}
    exec(compile(code, "<exported_script>", "exec"), namespace)
    return namespace["run_pipeline"](image)


class TestLineSegmentDetector:
    @pytest.fixture
    def test_lines_image(self):
        # Create an image with crisp horizontal and vertical line segments
        img = np.zeros((80, 80, 3), dtype=np.uint8)
        cv2.line(img, (15, 20), (65, 20), (255, 255, 255), 2)
        cv2.line(img, (20, 15), (20, 65), (255, 255, 255), 2)
        return img

    @pytest.fixture
    def bgra_image(self, test_lines_image):
        alpha = np.full((80, 80, 1), 220, dtype=np.uint8)
        return np.concatenate([test_lines_image, alpha], axis=2)

    @pytest.fixture
    def gray_2d(self, test_lines_image):
        return cv2.cvtColor(test_lines_image, cv2.COLOR_BGR2GRAY)

    @pytest.fixture
    def gray_3d(self, gray_2d):
        return gray_2d[:, :, np.newaxis]

    def test_bgr_line_detection(self, test_lines_image):
        op = LineSegmentDetector({"refine": "STD", "scale": 0.8, "lineColor": "#FF0000", "thickness": 2})
        result = op.compute(test_lines_image)
        assert result.shape == test_lines_image.shape
        assert result.dtype == np.uint8
        # Ensure red lines were drawn
        assert np.any(result[:, :, 2] > 0)

    def test_bgra_preserves_alpha(self, bgra_image):
        op = LineSegmentDetector({"refine": "STD", "scale": 0.8, "lineColor": "#00FF00", "thickness": 2})
        result = op.compute(bgra_image)
        assert result.shape == (80, 80, 4)
        np.testing.assert_array_equal(result[:, :, 3], bgra_image[:, :, 3])

    def test_grayscale_2d_promotes_to_bgr(self, gray_2d):
        op = LineSegmentDetector({"refine": "NONE", "scale": 0.8, "lineColor": "#0000FF", "thickness": 1})
        result = op.compute(gray_2d)
        assert result.shape == (80, 80, 3)
        assert result.dtype == np.uint8

    def test_grayscale_3d_promotes_to_bgr(self, gray_3d):
        op = LineSegmentDetector({"refine": "ADV", "scale": 0.8, "lineColor": "#00FF00", "thickness": 2})
        result = op.compute(gray_3d)
        assert result.shape == (80, 80, 3)
        assert result.dtype == np.uint8

    def test_refinement_modes(self, test_lines_image):
        for mode in ["NONE", "STD", "ADV"]:
            op = LineSegmentDetector({"refine": mode, "scale": 0.8})
            result = op.compute(test_lines_image)
            assert result.shape == test_lines_image.shape

    def test_blank_image_returns_clean_canvas(self):
        blank = np.zeros((50, 50, 3), dtype=np.uint8)
        op = LineSegmentDetector({"scale": 0.8})
        result = op.compute(blank)
        assert result.shape == blank.shape
        np.testing.assert_array_equal(result, blank)

    def test_invalid_input_raises(self):
        op = LineSegmentDetector({})
        with pytest.raises(ValueError, match="received an invalid or empty image"):
            op.compute(None)
        with pytest.raises(ValueError, match="received an invalid or empty image"):
            op.compute(np.array([], dtype=np.uint8))

    def test_exported_script_matches_operator(self, test_lines_image, bgra_image, gray_2d, gray_3d):
        params = {"refine": "STD", "scale": 0.8, "lineColor": "#00FF00", "thickness": 2}
        code, unsupported = export_pipeline_to_python(
            [PipelineStep(type="filtering_lsd", params=params)],
            "LSD Test",
        )
        assert unsupported == []
        expected_op = LineSegmentDetector(params)

        for img in [test_lines_image, bgra_image, gray_2d, gray_3d]:
            expected = expected_op.compute(img.copy())
            result = _run_exported_pipeline(code, img.copy())
            assert result.shape == expected.shape
            np.testing.assert_array_equal(result, expected)

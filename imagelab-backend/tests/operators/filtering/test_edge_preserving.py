import numpy as np
import pytest

from app.operators.filtering.edge_preserving import EdgePreservingFilter
from app.services.python_exporter.generator import PipelineStep, export_pipeline_to_python


def _run_exported_pipeline(code: str, image: np.ndarray) -> np.ndarray:
    namespace: dict = {}
    exec(compile(code, "<exported_script>", "exec"), namespace)
    return namespace["run_pipeline"](image)


class TestEdgePreservingFilter:
    @pytest.fixture
    def bgr_image(self):
        rng = np.random.default_rng(42)
        return rng.integers(0, 256, (40, 50, 3), dtype=np.uint8)

    @pytest.fixture
    def bgra_image(self, bgr_image):
        alpha = np.full((40, 50, 1), 180, dtype=np.uint8)
        return np.concatenate([bgr_image, alpha], axis=2)

    @pytest.fixture
    def gray_2d(self):
        rng = np.random.default_rng(42)
        return rng.integers(0, 256, (40, 50), dtype=np.uint8)

    @pytest.fixture
    def gray_3d(self, gray_2d):
        return gray_2d[:, :, np.newaxis]

    def test_bgr_recursive_filter(self, bgr_image):
        op = EdgePreservingFilter({"mode": "RECURS_FILTER", "sigma_s": 50, "sigma_r": 0.3})
        result = op.compute(bgr_image)
        assert result.shape == bgr_image.shape
        assert result.dtype == np.uint8

    def test_bgr_normconv_filter(self, bgr_image):
        op = EdgePreservingFilter({"mode": "NORMCONV_FILTER", "sigma_s": 40, "sigma_r": 0.5})
        result = op.compute(bgr_image)
        assert result.shape == bgr_image.shape
        assert result.dtype == np.uint8

    def test_bgra_preserves_alpha(self, bgra_image):
        op = EdgePreservingFilter({"mode": "RECURS_FILTER", "sigma_s": 60, "sigma_r": 0.4})
        result = op.compute(bgra_image)
        assert result.shape == (40, 50, 4)
        np.testing.assert_array_equal(result[:, :, 3], bgra_image[:, :, 3])

    def test_grayscale_2d(self, gray_2d):
        op = EdgePreservingFilter({"mode": "RECURS_FILTER", "sigma_s": 60, "sigma_r": 0.4})
        result = op.compute(gray_2d)
        assert result.shape == gray_2d.shape
        assert result.dtype == np.uint8

    def test_grayscale_3d(self, gray_3d):
        op = EdgePreservingFilter({"mode": "RECURS_FILTER", "sigma_s": 60, "sigma_r": 0.4})
        result = op.compute(gray_3d)
        assert result.shape == (40, 50, 1)
        assert result.dtype == np.uint8

    def test_parameter_clamping(self, bgr_image):
        op = EdgePreservingFilter({"mode": "invalid_mode", "sigma_s": -10, "sigma_r": 5.0})
        result = op.compute(bgr_image)
        assert result.shape == bgr_image.shape

    def test_empty_or_invalid_image_raises(self):
        op = EdgePreservingFilter({})
        with pytest.raises(ValueError, match="received an invalid or empty image"):
            op.compute(None)
        with pytest.raises(ValueError, match="received an invalid or empty image"):
            op.compute(np.array([], dtype=np.uint8))

    def test_exported_script_matches_operator(self, bgr_image, bgra_image, gray_2d, gray_3d):
        params = {"mode": "RECURS_FILTER", "sigma_s": 45, "sigma_r": 0.35}
        code, unsupported = export_pipeline_to_python(
            [PipelineStep(type="filtering_edgepreserving", params=params)],
            "Edge Preserving Test",
        )
        assert unsupported == []
        expected_op = EdgePreservingFilter(params)

        for img in [bgr_image, bgra_image, gray_2d, gray_3d]:
            expected = expected_op.compute(img.copy())
            result = _run_exported_pipeline(code, img.copy())
            assert result.shape == expected.shape
            np.testing.assert_array_equal(result, expected)

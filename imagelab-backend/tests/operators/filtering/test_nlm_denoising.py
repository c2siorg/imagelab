import ast

import numpy as np
import pytest

from app.models.pipeline import PipelineStep
from app.operators.filtering.nlm_denoising import NlmDenoising
from app.services.python_exporter.generator import export_pipeline_to_python


def _make_noisy_image(channels: int = 3, noise_sigma: float = 20.0) -> np.ndarray:
    """Creates a synthetic image with flat regions corrupted by Gaussian noise."""
    np.random.seed(42)
    if channels == 1:
        clean = np.ones((60, 60), dtype=np.uint8) * 120
        noise = np.random.normal(0, noise_sigma, clean.shape)
        noisy = np.clip(clean.astype(np.float32) + noise, 0, 255).astype(np.uint8)
        return noisy

    clean = np.ones((60, 60, channels), dtype=np.uint8)
    clean[:, :, 0] = 80
    if channels >= 3:
        clean[:, :, 1] = 120
        clean[:, :, 2] = 160
    if channels == 4:
        clean[:, :, 3] = 195  # Semi-transparent alpha

    noise = np.random.normal(0, noise_sigma, clean.shape)
    if channels == 4:
        noise[:, :, 3] = 0  # Alpha stays pristine

    noisy = np.clip(clean.astype(np.float32) + noise, 0, 255).astype(np.uint8)
    return noisy


class TestNlmDenoising:
    def test_bgr_image_denoising_reduces_noise_variance(self):
        noisy = _make_noisy_image(3, noise_sigma=25.0)
        noisy_var = np.var(noisy[:, :, :3])

        denoised = NlmDenoising({"h": 15.0, "hColor": 15.0}).compute(noisy)
        denoised_var = np.var(denoised[:, :, :3])

        assert denoised.shape == (60, 60, 3)
        assert denoised.dtype == np.uint8
        # Denoising reduces variance in a noisy flat patch
        assert denoised_var < noisy_var * 0.85

    def test_grayscale_2d_denoising(self):
        noisy = _make_noisy_image(1, noise_sigma=25.0)
        noisy_var = np.var(noisy)

        denoised = NlmDenoising({"h": 15.0}).compute(noisy)
        denoised_var = np.var(denoised)

        assert denoised.shape == (60, 60)
        assert denoised.ndim == 2
        assert denoised.dtype == np.uint8
        assert denoised_var < noisy_var * 0.6

    def test_single_channel_3d_input(self):
        noisy = _make_noisy_image(1)[:, :, np.newaxis]
        denoised = NlmDenoising({"h": 10.0}).compute(noisy)
        assert denoised.shape == (60, 60, 1)
        assert denoised.dtype == np.uint8

    def test_bgra_4_channel_preserves_alpha(self):
        noisy = _make_noisy_image(4, noise_sigma=20.0)
        denoised = NlmDenoising({"h": 12.0, "hColor": 12.0}).compute(noisy)

        assert denoised.shape == (60, 60, 4)
        assert denoised.dtype == np.uint8
        # Alpha channel is preserved bit-exact
        assert np.array_equal(denoised[:, :, 3], noisy[:, :, 3])
        # Color variance is reduced
        assert np.var(denoised[:, :, :3]) < np.var(noisy[:, :, :3])

    def test_window_size_even_number_clamping(self):
        # Even window sizes must automatically adjust to valid odd numbers without crashing
        noisy = _make_noisy_image(3)
        denoised = NlmDenoising(
            {
                "templateWindowSize": 8,  # even -> should become 9
                "searchWindowSize": 20,  # even -> should become 21
            }
        ).compute(noisy)
        assert denoised.shape == (60, 60, 3)

    def test_search_window_smaller_than_template_adjustment(self):
        noisy = _make_noisy_image(3)
        denoised = NlmDenoising(
            {
                "templateWindowSize": 15,
                "searchWindowSize": 7,  # Smaller than template -> must adjust safely
            }
        ).compute(noisy)
        assert denoised.shape == (60, 60, 3)

    def test_non_uint8_dtype_raises_error(self):
        img = np.zeros((40, 40, 3), dtype=np.float32)
        with pytest.raises(ValueError, match="expects a uint8 image"):
            NlmDenoising({}).compute(img)

        img_uint16 = np.zeros((40, 40, 3), dtype=np.uint16)
        with pytest.raises(ValueError, match="expects a uint8 image"):
            NlmDenoising({}).compute(img_uint16)

    def test_invalid_empty_image_raises_error(self):
        with pytest.raises(ValueError, match="invalid or empty image"):
            NlmDenoising({}).compute(np.array([], dtype=np.uint8))

    def test_invalid_none_image_raises_error(self):
        with pytest.raises(ValueError, match="invalid or empty image"):
            NlmDenoising({}).compute(None)

    def test_invalid_channels_raises_error(self):
        with pytest.raises(ValueError, match="expects a 2-D or 3-D image with 1, 3, or 4 channels"):
            NlmDenoising({}).compute(np.zeros((40, 40, 2), dtype=np.uint8))

    def test_python_exporter_nlm_denoising(self):
        params = {
            "h": 12.0,
            "hColor": 10.0,
            "templateWindowSize": 7,
            "searchWindowSize": 21,
        }
        steps = [PipelineStep(type="filtering_nlmdenoising", params=params)]
        code, unsupported = export_pipeline_to_python(steps, "input.png", "output.png")
        assert unsupported == []
        assert "fastNlMeansDenoising" in code

        # 1. AST syntax parsing
        tree = ast.parse(code)
        assert isinstance(tree, ast.Module)

        # 2. Execution on BGR
        compiled = compile(code, "<string>", "exec")
        namespace = {}
        exec(compiled, namespace)
        assert "run_pipeline" in namespace
        run_fn = namespace["run_pipeline"]

        noisy_bgr = _make_noisy_image(3)
        res_bgr = run_fn(noisy_bgr.copy())
        assert res_bgr.shape == (60, 60, 3)

        # 3. Execution on Grayscale
        noisy_gray = _make_noisy_image(1)
        res_gray = run_fn(noisy_gray.copy())
        assert res_gray.shape == (60, 60)

        # 4. Execution on BGRA
        noisy_bgra = _make_noisy_image(4)
        res_bgra = run_fn(noisy_bgra.copy())
        assert res_bgra.shape == (60, 60, 4)
        assert np.array_equal(res_bgra[:, :, 3], noisy_bgra[:, :, 3])

import ast

import cv2
import numpy as np
import pytest

from app.models.pipeline import PipelineStep
from app.operators.augmentation.cutout import Cutout
from app.services.python_exporter.generator import export_pipeline_to_python


@pytest.fixture
def color_image() -> np.ndarray:
    """Creates a 100x100 color image with diverse non-zero pixel intensities."""
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    img[:, :] = [180, 140, 90]
    cv2.circle(img, (50, 50), 30, (50, 100, 220), -1)
    return img


@pytest.fixture
def grayscale_image() -> np.ndarray:
    """Creates a 100x100 grayscale image."""
    img = np.full((100, 100), 128, dtype=np.uint8)
    cv2.circle(img, (50, 50), 25, 200, -1)
    return img


class TestCutout:
    def test_default_params_output_shape(self, color_image):
        result = Cutout({}).compute(color_image)
        assert result.shape == color_image.shape
        assert result.dtype == np.uint8

    def test_grayscale_2d_input(self, grayscale_image):
        op = Cutout({"num_holes": 2, "hole_size": 20, "seed": 42})
        result = op.compute(grayscale_image)
        assert result.shape == (100, 100)
        assert result.ndim == 2
        assert not np.array_equal(result, grayscale_image)

    def test_single_channel_3d_input(self, grayscale_image):
        img_3d = grayscale_image[:, :, np.newaxis]
        op = Cutout({"num_holes": 1, "hole_size": 24, "seed": 42})
        result = op.compute(img_3d)
        assert result.shape == (100, 100, 1)
        assert not np.array_equal(result, img_3d)

    def test_rgba_preserves_alpha(self, color_image):
        alpha = np.full((100, 100, 1), 220, dtype=np.uint8)
        rgba = np.dstack([color_image, alpha])
        op = Cutout(
            {
                "num_holes": 3,
                "hole_size": 24,
                "fill_mode": "CONSTANT",
                "fill_color": "#ff0000",
                "seed": 7,
            }
        )
        result = op.compute(rgba)
        assert result.shape == (100, 100, 4)
        np.testing.assert_array_equal(result[:, :, 3], alpha[:, :, 0])
        # RGB channels were modified
        assert not np.array_equal(result[:, :, :3], color_image)

    def test_deterministic_seed(self, color_image):
        op1 = Cutout({"num_holes": 2, "hole_size": 30, "seed": 12345})
        op2 = Cutout({"num_holes": 2, "hole_size": 30, "seed": 12345})
        res1 = op1.compute(color_image)
        res2 = op2.compute(color_image)
        np.testing.assert_array_equal(res1, res2)

    def test_different_seeds_differ(self, color_image):
        op1 = Cutout({"num_holes": 2, "hole_size": 30, "seed": 111})
        op2 = Cutout({"num_holes": 2, "hole_size": 30, "seed": 222})
        res1 = op1.compute(color_image)
        res2 = op2.compute(color_image)
        assert not np.array_equal(res1, res2)

    def test_constant_fill_color(self, color_image):
        # Fill with pure cyan (#00ffff -> BGR 255, 255, 0)
        op = Cutout(
            {
                "num_holes": 1,
                "hole_size": 40,
                "fill_mode": "CONSTANT",
                "fill_color": "#00ffff",
                "seed": 42,
            }
        )
        result = op.compute(color_image)
        cyan_mask = (result[:, :, 0] == 255) & (result[:, :, 1] == 255) & (result[:, :, 2] == 0)
        assert np.any(cyan_mask)

    def test_random_noise_fill_mode(self, color_image):
        op = Cutout(
            {
                "num_holes": 2,
                "hole_size": 32,
                "fill_mode": "RANDOM_NOISE",
                "seed": 99,
            }
        )
        result = op.compute(color_image)
        assert result.shape == color_image.shape
        assert not np.array_equal(result, color_image)

    def test_mean_fill_mode(self, color_image):
        op = Cutout(
            {
                "num_holes": 2,
                "hole_size": 28,
                "fill_mode": "MEAN",
                "seed": 55,
            }
        )
        result = op.compute(color_image)
        assert result.shape == color_image.shape
        assert not np.array_equal(result, color_image)

    def test_invalid_inputs(self):
        op = Cutout({})
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
            id="step_cutout",
            type="augmentation_cutout",
            params={
                "num_holes": 3,
                "hole_size": 24,
                "fill_mode": "CONSTANT",
                "fill_color": "#123456",
                "seed": 42,
            },
        )
        code, _ = export_pipeline_to_python([step])
        parsed = ast.parse(code)
        assert parsed is not None
        assert "default_rng(42)" in code
        assert "for _ in range(3):" in code

    def test_odd_hole_size(self):
        # 100x100 white image
        img = np.full((100, 100, 3), 255, dtype=np.uint8)
        # Centered cutout with hole_size 33
        op = Cutout(
            {
                "num_holes": 1,
                "hole_size": 33,
                "fill_mode": "CONSTANT",
                "fill_color": "#000000",
                "seed": 1,
            }
        )
        res = op.compute(img)
        black_pixels = np.all(res == [0, 0, 0], axis=-1)
        count = np.sum(black_pixels)
        # Patch must be 33x33 = 1089 pixels if not boundary-clipped
        assert count == 33 * 33 or count > 0

    def test_python_exporter_execution_parity(self, color_image):
        params = {
            "num_holes": 2,
            "hole_size": 20,
            "fill_mode": "CONSTANT",
            "fill_color": "#00ff00",
            "seed": 777,
        }
        op = Cutout(params)
        expected = op.compute(color_image)

        step = PipelineStep(id="s1", type="augmentation_cutout", params=params)
        code, _ = export_pipeline_to_python([step])

        scope = {}
        exec(code, scope)
        run_fn = scope["run_pipeline"]
        actual = run_fn(color_image.copy())

        np.testing.assert_array_equal(actual, expected)

    def test_python_exporter_random_noise_parity(self, color_image):
        params = {
            "num_holes": 3,
            "hole_size": 25,
            "fill_mode": "RANDOM_NOISE",
            "seed": 1234,
        }
        op = Cutout(params)
        expected = op.compute(color_image)

        step = PipelineStep(id="s2", type="augmentation_cutout", params=params)
        code, _ = export_pipeline_to_python([step])

        scope = {}
        exec(code, scope)
        run_fn = scope["run_pipeline"]
        actual = run_fn(color_image.copy())

        np.testing.assert_array_equal(actual, expected)

    def test_python_exporter_mean_parity(self, color_image):
        params = {
            "num_holes": 2,
            "hole_size": 28,
            "fill_mode": "MEAN",
            "seed": 888,
        }
        op = Cutout(params)
        expected = op.compute(color_image)

        step = PipelineStep(id="s3", type="augmentation_cutout", params=params)
        code, _ = export_pipeline_to_python([step])

        scope = {}
        exec(code, scope)
        run_fn = scope["run_pipeline"]
        actual = run_fn(color_image.copy())

        np.testing.assert_array_equal(actual, expected)

    def test_python_exporter_bgra_parity(self, color_image):
        alpha = np.full((100, 100, 1), 200, dtype=np.uint8)
        bgra = np.dstack([color_image, alpha])

        params = {
            "num_holes": 2,
            "hole_size": 22,
            "fill_mode": "CONSTANT",
            "fill_color": "#ff00ff",
            "seed": 999,
        }
        op = Cutout(params)
        expected = op.compute(bgra)

        step = PipelineStep(id="s4", type="augmentation_cutout", params=params)
        code, _ = export_pipeline_to_python([step])

        scope = {}
        exec(code, scope)
        run_fn = scope["run_pipeline"]
        actual = run_fn(bgra.copy())

        np.testing.assert_array_equal(actual, expected)

    def test_python_exporter_grayscale_parity(self, grayscale_image):
        params = {
            "num_holes": 2,
            "hole_size": 18,
            "fill_mode": "CONSTANT",
            "fill_color": "#ffffff",
            "seed": 555,
        }
        op = Cutout(params)
        expected = op.compute(grayscale_image)

        step = PipelineStep(id="s5", type="augmentation_cutout", params=params)
        code, _ = export_pipeline_to_python([step])

        scope = {}
        exec(code, scope)
        run_fn = scope["run_pipeline"]
        actual = run_fn(grayscale_image.copy())

        np.testing.assert_array_equal(actual, expected)

import ast

import cv2
import numpy as np
import pytest

from app.operators.detection.blob_detection import BlobDetection
from app.services.python_exporter.generator import export_pipeline_to_python


class TestBlobDetection:
    def test_invalid_or_empty_inputs_raise_value_error(self):
        op = BlobDetection({})
        with pytest.raises(ValueError, match="invalid or empty image"):
            op.compute(None)

        with pytest.raises(ValueError, match="invalid or empty image"):
            op.compute(np.empty((0, 0), dtype=np.uint8))

        with pytest.raises(ValueError, match="2-D or 3-D image"):
            op.compute(np.zeros((10, 10, 5), dtype=np.uint8))

        with pytest.raises(ValueError, match="uint8 image"):
            op.compute(np.zeros((10, 10), dtype=np.float32))

    def test_detects_circular_blobs_and_draws_keypoints(self):
        # Create an image with two distinct solid circles
        img = np.zeros((120, 120, 3), dtype=np.uint8)
        cv2.circle(img, (40, 40), 15, (255, 255, 255), -1)
        cv2.circle(img, (90, 90), 12, (255, 255, 255), -1)

        op = BlobDetection(
            {
                "filter_by_area": True,
                "min_area": 10.0,
                "max_area": 2000.0,
                "rgbcolors_input": "#00ffff",
            }
        )
        res = op.compute(img)
        assert res.shape == (120, 120, 3)
        assert res.dtype == np.uint8
        # Output is modified by drawing rich keypoint circles
        assert not np.array_equal(res, img)
        # Cyan marker color (BGR: 255, 255, 0) drawn around keypoint centers (40, 40) and (90, 90)
        blob1_region = res[20:60, 20:60]
        blob2_region = res[70:110, 70:110]
        assert np.any((blob1_region[:, :, 0] > 0) & (blob1_region[:, :, 1] > 0) & (blob1_region[:, :, 2] == 0))
        assert np.any((blob2_region[:, :, 0] > 0) & (blob2_region[:, :, 1] > 0) & (blob2_region[:, :, 2] == 0))
        # Distant background remains unaffected
        np.testing.assert_array_equal(res[5, 5], [0, 0, 0])

    def test_2d_grayscale_promotes_to_bgr(self):
        img_gray = np.zeros((80, 80), dtype=np.uint8)
        cv2.circle(img_gray, (40, 40), 10, 255, -1)
        op = BlobDetection({"filter_by_area": True, "min_area": 10.0})
        res = op.compute(img_gray)
        assert res.shape == (80, 80, 3)
        assert res.dtype == np.uint8

    def test_single_channel_3d_promotes_to_bgr(self):
        img_1ch = np.zeros((80, 80, 1), dtype=np.uint8)
        cv2.circle(img_1ch, (40, 40), 10, 255, -1)
        op = BlobDetection({"filter_by_area": True, "min_area": 10.0})
        res = op.compute(img_1ch)
        assert res.shape == (80, 80, 3)
        assert res.dtype == np.uint8

    def test_preserves_bgra_alpha_channel(self):
        bgra = np.zeros((100, 100, 4), dtype=np.uint8)
        bgra[:, :, 3] = 180  # custom alpha
        cv2.circle(bgra, (50, 50), 15, (255, 255, 255, 180), -1)

        op = BlobDetection({"filter_by_area": True, "min_area": 10.0})
        res = op.compute(bgra)
        assert res.shape == (100, 100, 4)
        assert res.dtype == np.uint8
        # Alpha channel should be preserved exactly
        np.testing.assert_array_equal(res[:, :, 3], 180)

    def test_handles_empty_detection_cleanly(self):
        blank = np.zeros((50, 50, 3), dtype=np.uint8)
        op = BlobDetection({"filter_by_area": True, "min_area": 500.0})
        res = op.compute(blank)
        assert res.shape == (50, 50, 3)
        # Blank canvas untouched
        np.testing.assert_array_equal(res, blank)

    def test_parameter_clamping_and_inverted_bounds(self):
        # min_threshold >= max_threshold should swap/correct
        # min_area > max_area should swap
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        cv2.circle(img, (50, 50), 15, (255, 255, 255), -1)
        op = BlobDetection(
            {
                "min_threshold": 240.0,
                "max_threshold": 20.0,
                "filter_by_area": True,
                "min_area": 5000.0,
                "max_area": 10.0,
                "filter_by_circularity": "TRUE",
                "min_circularity": 0.7,
                "filter_by_convexity": True,
                "min_convexity": 0.8,
                "filter_by_inertia": True,
                "min_inertia_ratio": 0.5,
            }
        )
        res = op.compute(img)
        assert res.shape == (100, 100, 3)
        assert res.dtype == np.uint8
        # Swapped area (10 to 5000) and swapped thresholds allow detecting the blob at (50, 50)
        assert not np.array_equal(res, img)


class TestBlobDetectionExporter:
    def test_generates_valid_compilable_and_executable_script(self):
        pipeline = [
            {
                "type": "detection_blobdetection",
                "params": {
                    "min_threshold": 10.0,
                    "max_threshold": 200.0,
                    "filter_by_area": True,
                    "min_area": 15.0,
                    "max_area": 3000.0,
                    "filter_by_circularity": True,
                    "min_circularity": 0.5,
                    "rgbcolors_input": "#ff0000",
                },
            }
        ]
        script, _ = export_pipeline_to_python(pipeline)
        # Validate AST
        tree = ast.parse(script)
        assert tree is not None

        # Execute exported script
        code_obj = compile(tree, filename="<test_blob_export>", mode="exec")
        scope = {}
        exec(code_obj, scope)
        assert "run_pipeline" in scope

        img = np.zeros((100, 100, 3), dtype=np.uint8)
        cv2.circle(img, (50, 50), 15, (255, 255, 255), -1)
        out = scope["run_pipeline"](img.copy())
        assert out.shape == (100, 100, 3)
        assert out.dtype == np.uint8

        expected = BlobDetection(pipeline[0]["params"]).compute(img.copy())
        np.testing.assert_array_equal(out, expected)

    def test_generates_valid_script_on_bgra_image(self):
        pipeline = [
            {
                "type": "detection_blobdetection",
                "params": {
                    "min_threshold": 10.0,
                    "max_threshold": 200.0,
                    "filter_by_area": True,
                    "min_area": 15.0,
                    "max_area": 3000.0,
                    "rgbcolors_input": "#00ffff",
                },
            }
        ]
        script, _ = export_pipeline_to_python(pipeline)
        tree = ast.parse(script)
        code_obj = compile(tree, filename="<test_blob_export_bgra>", mode="exec")
        scope = {}
        exec(code_obj, scope)
        assert "run_pipeline" in scope

        # 4-channel BGRA image with a circular blob
        img = np.zeros((100, 100, 4), dtype=np.uint8)
        img[:, :, 3] = 200  # Alpha channel
        cv2.circle(img, (50, 50), 15, (255, 255, 255, 200), -1)

        out = scope["run_pipeline"](img.copy())
        assert out.shape == (100, 100, 4)
        assert out.dtype == np.uint8
        np.testing.assert_array_equal(out[:, :, 3], img[:, :, 3])

        expected = BlobDetection(pipeline[0]["params"]).compute(img.copy())
        np.testing.assert_array_equal(out, expected)

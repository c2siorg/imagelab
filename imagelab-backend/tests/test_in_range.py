import ast
from textwrap import dedent

import cv2
import numpy as np

from app.operators.registry import get_operator
from app.services.python_exporter.templates import OPERATOR_TEMPLATES


class TestInRangeThreshold:
    def test_uniform_color_segmentation_returns_binary_mask(self):
        image = np.array([[(0, 255, 0), (255, 0, 0)]], dtype=np.uint8)
        result = get_operator("thresholding_inrange")(
            {
                "h_min": 55,
                "h_max": 65,
                "s_min": 200,
                "s_max": 255,
                "v_min": 200,
                "v_max": 255,
                "output_mask_only": True,
            }
        ).compute(image)

        assert result.shape == (1, 2)
        assert result.dtype == np.uint8
        np.testing.assert_array_equal(result, np.array([[255, 0]], dtype=np.uint8))

    def test_masked_output_matches_bitwise_and(self):
        image = np.array([[(0, 255, 0), (255, 0, 0)]], dtype=np.uint8)
        result = get_operator("thresholding_inrange")(
            {
                "h_min": 55,
                "h_max": 65,
                "s_min": 200,
                "s_max": 255,
                "v_min": 200,
                "v_max": 255,
            }
        ).compute(image)
        expected_mask = cv2.inRange(
            cv2.cvtColor(image, cv2.COLOR_BGR2HSV),
            np.array([55, 200, 200], dtype=np.uint8),
            np.array([65, 255, 255], dtype=np.uint8),
        )

        np.testing.assert_array_equal(result, cv2.bitwise_and(image, image, mask=expected_mask))

    def test_bgra_output_preserves_alpha(self):
        bgr = np.array([[(0, 255, 0), (255, 0, 0)]], dtype=np.uint8)
        alpha = np.array([[17, 231]], dtype=np.uint8)
        image = np.dstack([bgr, alpha])
        result = get_operator("thresholding_inrange")(
            {
                "h_min": 55,
                "h_max": 65,
                "s_min": 200,
                "s_max": 255,
                "v_min": 200,
                "v_max": 255,
            }
        ).compute(image)

        assert result.shape == image.shape
        np.testing.assert_array_equal(result[:, :, 3], alpha)

    def test_grayscale_input_is_promoted_to_bgr(self):
        image = np.array([[0, 128, 255]], dtype=np.uint8)
        result = get_operator("thresholding_inrange")(
            {
                "h_min": 0,
                "h_max": 179,
                "s_min": 0,
                "s_max": 0,
                "v_min": 100,
                "v_max": 200,
                "output_mask_only": True,
            }
        ).compute(image)

        np.testing.assert_array_equal(result, np.array([[0, 255, 0]], dtype=np.uint8))

    def test_parameters_are_clamped_to_opencv_ranges(self):
        image = np.array([[(0, 255, 0)]], dtype=np.uint8)
        operator = get_operator("thresholding_inrange")
        result = operator(
            {
                "h_min": -10,
                "h_max": 999,
                "s_min": -1,
                "s_max": 999,
                "v_min": -1,
                "v_max": 999,
                "output_mask_only": True,
            }
        ).compute(image)
        expected = operator(
            {
                "h_min": 0,
                "h_max": 179,
                "s_min": 0,
                "s_max": 255,
                "v_min": 0,
                "v_max": 255,
                "output_mask_only": True,
            }
        ).compute(image)

        np.testing.assert_array_equal(result, expected)


class TestInRangeExporter:
    def test_template_is_registered_and_executes(self):
        template = OPERATOR_TEMPLATES["thresholding_inrange"]
        lines, needs_numpy = template(
            {
                "h_min": 55,
                "h_max": 65,
                "s_min": 200,
                "s_max": 255,
                "v_min": 200,
                "v_max": 255,
                "output_mask_only": True,
            },
            "image",
        )
        code = dedent("\n".join(lines))

        tree = ast.parse(code)
        compiled = compile(tree, "<in_range_template>", "exec")
        assert needs_numpy is True

        image = np.array([[(0, 255, 0), (255, 0, 0)]], dtype=np.uint8)
        namespace = {"cv2": cv2, "np": np, "image": image}
        exec(compiled, namespace)

        np.testing.assert_array_equal(namespace["image"], np.array([[255, 0]], dtype=np.uint8))

from unittest.mock import patch

import numpy as np

from app.models.pipeline import PipelineRequest, PipelineStep
from app.services.pipeline_executor import execute_pipeline
from app.utils.image import encode_image_base64


def _make_request(include_intermediates: bool = False) -> PipelineRequest:
    img = np.full((10, 10, 3), 128, dtype=np.uint8)
    b64 = encode_image_base64(img, "png")
    return PipelineRequest(
        image=b64,
        image_format="png",
        pipeline=[
            PipelineStep(type="blurring_applyblur", params={"widthSize": 3, "heightSize": 3}),
            PipelineStep(type="imageconvertions_grayimage", params={}),
        ],
        include_intermediates=include_intermediates,
    )


class TestIntermediatesFlag:
    def test_intermediates_absent_by_default(self):
        result = execute_pipeline(_make_request(include_intermediates=False))
        assert result.success
        assert result.intermediates is None

    def test_intermediates_present_when_requested(self):
        result = execute_pipeline(_make_request(include_intermediates=True))
        assert result.success
        assert result.intermediates is not None
        assert len(result.intermediates) == 2

    def test_intermediates_step_numbers(self):
        result = execute_pipeline(_make_request(include_intermediates=True))
        steps = [r.step for r in result.intermediates]
        assert steps == [1, 2]

    def test_intermediates_operator_types(self):
        result = execute_pipeline(_make_request(include_intermediates=True))
        types = [r.operator_type for r in result.intermediates]
        assert types == ["blurring_applyblur", "imageconvertions_grayimage"]

    def test_each_intermediate_has_thumbnail(self):
        result = execute_pipeline(_make_request(include_intermediates=True))
        for step_result in result.intermediates:
            assert step_result.thumbnail != ""

    def test_each_intermediate_has_stats(self):
        result = execute_pipeline(_make_request(include_intermediates=True))
        for step_result in result.intermediates:
            s = step_result.stats
            assert s.width == 10
            assert s.height == 10
            assert len(s.histograms) >= 1

    def test_final_image_still_returned(self):
        result = execute_pipeline(_make_request(include_intermediates=True))
        assert result.image is not None

    def test_intermediate_capture_failure_does_not_fail_pipeline(self):
        with patch("app.services.pipeline_executor.compute_image_stats", side_effect=RuntimeError("boom")):
            result = execute_pipeline(_make_request(include_intermediates=True))
        assert result.success
        assert result.image is not None

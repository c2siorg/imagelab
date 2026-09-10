import numpy as np
import pytest

from app.exceptions import MemoryLimitExceededException
from app.models.pipeline import PipelineRequest, PipelineStep
from app.services.pipeline_executor import check_memory_limit, execute_pipeline
from app.utils.image import encode_image_base64


def test_memory_limit_exceeded_exception_direct_check():
    """Verify check_memory_limit raises MemoryLimitExceededException when byte footprint exceeds threshold."""
    # Create image exceeding default limit (50 MB) e.g., 5000 x 5000 x 3 = ~75 MB
    large_img = np.zeros((5000, 5000, 3), dtype=np.uint8)
    assert large_img.nbytes > 50 * 1024 * 1024

    with pytest.raises(MemoryLimitExceededException) as exc_info:
        check_memory_limit(large_img)

    assert "memory footprint" in str(exc_info.value).lower()
    assert "exceeds" in str(exc_info.value).lower()

    # Custom lower threshold (1 MB)
    medium_img = np.zeros((1000, 1000, 3), dtype=np.uint8)  # ~3 MB
    with pytest.raises(MemoryLimitExceededException):
        check_memory_limit(medium_img, max_bytes=1 * 1024 * 1024)


def test_memory_limit_exceeded_during_pipeline_execution():
    """Verify execute_pipeline raises MemoryLimitExceededException when given an oversized image."""
    # Create ~60 MB image (4500 x 4500 x 3 uint8)
    large_img = np.full((4500, 4500, 3), 128, dtype=np.uint8)
    large_b64 = encode_image_base64(large_img, "png")

    req = PipelineRequest(
        image=large_b64,
        image_format="png",
        pipeline=[PipelineStep(block_id="step_gray", type="imageconvertions_grayimage")],
    )

    with pytest.raises(MemoryLimitExceededException):
        execute_pipeline(req)

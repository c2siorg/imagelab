import numpy as np
import pytest

from app.exceptions import MemoryLimitExceededException
from app.operators.geometric.resize_image import ResizeImage
from app.operators.geometric.rotate_image import RotateImage
from app.operators.geometric.scale_image import ScaleImage


@pytest.fixture
def image() -> np.ndarray:
    return np.zeros((1080, 1920, 3), dtype=np.uint8)


def test_scale_image_rejects_oversized_output_before_allocating(image, monkeypatch) -> None:
    def fail(*args, **kwargs):
        raise AssertionError("cv2.resize must not run for an oversized output")

    monkeypatch.setattr("app.operators.geometric.scale_image.cv2.resize", fail)
    with pytest.raises(MemoryLimitExceededException, match="2488320000 bytes"):
        ScaleImage({"fx": 20, "fy": 20}).compute(image)


def test_resize_image_rejects_oversized_output_before_allocating(image, monkeypatch) -> None:
    def fail(*args, **kwargs):
        raise AssertionError("cv2.resize must not run for an oversized output")

    monkeypatch.setattr("app.operators.geometric.resize_image.cv2.resize", fail)
    with pytest.raises(MemoryLimitExceededException):
        ResizeImage({"width": 40000, "height": 20000}).compute(image)


def test_rotate_image_rejects_oversized_output_before_allocating(image, monkeypatch) -> None:
    def fail(*args, **kwargs):
        raise AssertionError("cv2.warpAffine must not run for an oversized output")

    monkeypatch.setattr("app.operators.geometric.rotate_image.cv2.warpAffine", fail)
    with pytest.raises(MemoryLimitExceededException):
        RotateImage({"angle": 45, "scale": 10}).compute(image)


def test_outputs_within_limit_still_work(image) -> None:
    assert ScaleImage({"fx": 2, "fy": 2}).compute(image).shape == (2160, 3840, 3)
    assert ResizeImage({"width": 100, "height": 50}).compute(image).shape == (50, 100, 3)
    assert RotateImage({"angle": 90}).compute(image).shape == (1920, 1080, 3)

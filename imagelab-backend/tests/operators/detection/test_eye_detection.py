import cv2
import numpy as np
import pytest

from app.operators.detection.eye_detection import EyeDetection, filter_eye_candidates


class FakeCascade:
    def __init__(self, eyes: list[tuple[int, int, int, int]]):
        self.eyes = np.array(eyes, dtype=np.int32)

    def detectMultiScale(self, *_args, **_kwargs):
        return self.eyes


def test_eye_detection_draws_rectangles(monkeypatch):
    monkeypatch.setattr(
        "app.operators.detection.eye_detection.load_eye_cascade",
        lambda: FakeCascade([(10, 12, 24, 16)]),
    )
    image = np.zeros((60, 60, 3), dtype=np.uint8)

    result = EyeDetection(
        {
            "scaleFactor": 1.2,
            "minNeighbors": 8,
            "minSize": 20,
            "rgbcolors_input": "#00ff00",
            "thickness": 5,
        }
    ).compute(image)

    assert result.shape == image.shape
    assert result.dtype == image.dtype
    assert np.count_nonzero(result[:, :, 1]) > 0


def test_eye_detection_returns_bgr_output_for_grayscale(monkeypatch):
    monkeypatch.setattr(
        "app.operators.detection.eye_detection.load_eye_cascade",
        lambda: FakeCascade([]),
    )
    image = np.zeros((40, 40), dtype=np.uint8)

    result = EyeDetection({}).compute(image)

    assert result.shape == (40, 40, 3)


def test_eye_detection_scales_boxes_back_to_original_size(monkeypatch):
    monkeypatch.setattr(
        "app.operators.detection.eye_detection.load_eye_cascade",
        lambda: FakeCascade([(18, 24, 30, 18)]),
    )
    image = np.zeros((2000, 1000, 3), dtype=np.uint8)

    result = EyeDetection({"minSize": 24, "thickness": 5, "rgbcolors_input": "#00ff00"}).compute(image)

    green_mask = result[:, :, 1] > 0
    x, y, w, h = cv2.boundingRect(green_mask.astype(np.uint8))
    assert abs(x - 50) <= 1
    assert abs(y - 67) <= 1
    assert abs(w - 83) <= 3
    assert abs(h - 50) <= 3


def test_filter_eye_candidates_rejects_unlikely_aspect_ratios():
    eyes = np.array(
        [
            (10, 10, 36, 20),
            (20, 20, 120, 20),
            (30, 30, 20, 70),
        ],
        dtype=np.int32,
    )

    assert filter_eye_candidates(eyes) == [(10, 10, 36, 20)]


@pytest.mark.parametrize(
    ("params", "message"),
    [
        ({"scaleFactor": 1.0}, "scaleFactor"),
        ({"minNeighbors": -1}, "minNeighbors"),
        ({"minSize": -5}, "minSize"),
        ({"thickness": 0}, "thickness"),
    ],
)
def test_eye_detection_validates_params(monkeypatch, params, message):
    monkeypatch.setattr(
        "app.operators.detection.eye_detection.load_eye_cascade",
        lambda: FakeCascade([]),
    )

    with pytest.raises(ValueError, match=message):
        EyeDetection(params).compute(np.zeros((20, 20, 3), dtype=np.uint8))

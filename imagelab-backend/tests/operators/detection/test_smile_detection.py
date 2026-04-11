import cv2
import numpy as np
import pytest

from app.operators.detection.smile_detection import (
    SmileDetection,
    choose_best_smile,
    filter_face_candidates,
    filter_smile_candidates,
)


class FakeCascade:
    def __init__(self, results: list[tuple[int, int, int, int]]):
        self.results = np.array(results, dtype=np.int32)

    def detectMultiScale(self, *_args, **_kwargs):
        return self.results


def test_smile_detection_draws_rectangles(monkeypatch):
    monkeypatch.setattr(
        "app.operators.detection.smile_detection.load_face_cascade",
        lambda: FakeCascade([(10, 10, 60, 60)]),
    )
    monkeypatch.setattr(
        "app.operators.detection.smile_detection.load_smile_cascade",
        lambda: FakeCascade([(12, 8, 28, 12)]),
    )
    image = np.zeros((100, 100, 3), dtype=np.uint8)

    result = SmileDetection(
        {
            "scaleFactor": 1.6,
            "minNeighbors": 18,
            "minSize": 20,
            "rgbcolors_input": "#00ff00",
            "thickness": 2,
        }
    ).compute(image)

    assert result.shape == image.shape
    assert result.dtype == image.dtype
    assert np.count_nonzero(result[:, :, 1]) > 0


def test_smile_detection_returns_bgr_output_for_grayscale(monkeypatch):
    monkeypatch.setattr(
        "app.operators.detection.smile_detection.load_face_cascade",
        lambda: FakeCascade([]),
    )
    monkeypatch.setattr(
        "app.operators.detection.smile_detection.load_smile_cascade",
        lambda: FakeCascade([]),
    )
    image = np.zeros((40, 40), dtype=np.uint8)

    result = SmileDetection({}).compute(image)

    assert result.shape == (40, 40, 3)


def test_smile_detection_scales_boxes_back_to_original_size(monkeypatch):
    monkeypatch.setattr(
        "app.operators.detection.smile_detection.load_face_cascade",
        lambda: FakeCascade([(18, 18, 72, 72)]),
    )
    monkeypatch.setattr(
        "app.operators.detection.smile_detection.load_smile_cascade",
        lambda: FakeCascade([(16, 6, 32, 12)]),
    )
    image = np.zeros((2000, 1000, 3), dtype=np.uint8)

    result = SmileDetection({"minSize": 24, "thickness": 2, "rgbcolors_input": "#00ff00"}).compute(image)

    green_mask = result[:, :, 1] > 0
    x, y, w, h = cv2.boundingRect(green_mask.astype(np.uint8))
    assert abs(x - 94) <= 2
    assert abs(y - 158) <= 4
    assert abs(w - 90) <= 4
    assert abs(h - 36) <= 4


def test_filter_face_candidates_rejects_unlikely_aspect_ratios():
    faces = np.array(
        [
            (10, 10, 60, 60),
            (20, 20, 120, 40),
            (30, 30, 35, 70),
        ],
        dtype=np.int32,
    )

    assert filter_face_candidates(faces) == [(10, 10, 60, 60)]


def test_filter_smile_candidates_rejects_unlikely_shapes():
    smiles = np.array(
        [
            (10, 10, 30, 12),
            (20, 20, 80, 10),
            (30, 30, 8, 20),
        ],
        dtype=np.int32,
    )

    assert filter_smile_candidates(smiles, 60, 60) == [(10, 10, 30, 12)]


def test_choose_best_smile_prefers_largest_area():
    smiles = [(10, 10, 20, 10), (12, 8, 30, 12)]

    assert choose_best_smile(smiles) == (12, 8, 30, 12)


@pytest.mark.parametrize(
    ("params", "message"),
    [
        ({"scaleFactor": 1.0}, "scaleFactor"),
        ({"minNeighbors": -1}, "minNeighbors"),
        ({"minSize": -5}, "minSize"),
        ({"thickness": 0}, "thickness"),
    ],
)
def test_smile_detection_validates_params(monkeypatch, params, message):
    monkeypatch.setattr(
        "app.operators.detection.smile_detection.load_face_cascade",
        lambda: FakeCascade([]),
    )
    monkeypatch.setattr(
        "app.operators.detection.smile_detection.load_smile_cascade",
        lambda: FakeCascade([]),
    )

    with pytest.raises(ValueError, match=message):
        SmileDetection(params).compute(np.zeros((20, 20, 3), dtype=np.uint8))

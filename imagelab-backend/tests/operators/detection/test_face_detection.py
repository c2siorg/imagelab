import cv2
import numpy as np
import pytest

from app.operators.detection.face_detection import (
    FaceDetection,
    filter_face_candidates,
    resize_for_detection,
)


class FakeCascade:
    def __init__(self, faces: list[tuple[int, int, int, int]]):
        self.faces = np.array(faces, dtype=np.int32)

    def detectMultiScale(self, *_args, **_kwargs):
        return self.faces


def test_face_detection_draws_rectangles(monkeypatch):
    monkeypatch.setattr(
        "app.operators.detection.face_detection.load_face_cascade",
        lambda: FakeCascade([(10, 12, 20, 18)]),
    )
    image = np.zeros((60, 60, 3), dtype=np.uint8)

    result = FaceDetection(
        {
            "scaleFactor": 1.1,
            "minNeighbors": 5,
            "minSize": 20,
            "rgbcolors_input": "#00ff00",
            "thickness": 2,
        }
    ).compute(image)

    assert result.shape == image.shape
    assert result.dtype == image.dtype
    assert np.count_nonzero(result[:, :, 1]) > 0


def test_face_detection_returns_bgr_output_for_grayscale(monkeypatch):
    monkeypatch.setattr(
        "app.operators.detection.face_detection.load_face_cascade",
        lambda: FakeCascade([]),
    )
    image = np.zeros((40, 40), dtype=np.uint8)

    result = FaceDetection({}).compute(image)

    assert result.shape == (40, 40, 3)


def test_resize_for_detection_downscales_large_images():
    gray = np.zeros((2000, 1000), dtype=np.uint8)

    resized, scale, min_size = resize_for_detection(gray, 60)

    assert resized.shape[0] == 720
    assert resized.shape[1] == 360
    assert scale == pytest.approx(0.36)
    assert min_size == (22, 22)


def test_face_detection_scales_boxes_back_to_original_size(monkeypatch):
    monkeypatch.setattr(
        "app.operators.detection.face_detection.load_face_cascade",
        lambda: FakeCascade([(24, 36, 48, 60)]),
    )
    image = np.zeros((2000, 1000, 3), dtype=np.uint8)

    result = FaceDetection({"minSize": 60, "thickness": 2, "rgbcolors_input": "#00ff00"}).compute(image)

    green_mask = result[:, :, 1] > 0
    x, y, w, h = cv2.boundingRect(green_mask.astype(np.uint8))
    assert abs(x - 67) <= 1
    assert abs(y - 100) <= 1
    assert abs(w - 133) <= 3
    assert abs(h - 167) <= 3


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


@pytest.mark.parametrize(
    ("params", "message"),
    [
        ({"scaleFactor": 1.0}, "scaleFactor"),
        ({"minNeighbors": -1}, "minNeighbors"),
        ({"minSize": -5}, "minSize"),
        ({"thickness": 0}, "thickness"),
    ],
)
def test_face_detection_validates_params(monkeypatch, params, message):
    monkeypatch.setattr(
        "app.operators.detection.face_detection.load_face_cascade",
        lambda: FakeCascade([]),
    )

    with pytest.raises(ValueError, match=message):
        FaceDetection(params).compute(np.zeros((20, 20, 3), dtype=np.uint8))

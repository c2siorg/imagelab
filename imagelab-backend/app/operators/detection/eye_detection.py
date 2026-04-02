from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from app.operators.base import BaseOperator
from app.operators.detection.common import prepare_output, resize_for_detection, to_grayscale
from app.utils.color import hex_to_bgr

_CASCADE_PATH = Path(cv2.data.haarcascades) / "haarcascade_eye.xml"
MIN_EYE_ASPECT_RATIO = 0.45
MAX_EYE_ASPECT_RATIO = 2.4


def load_eye_cascade() -> cv2.CascadeClassifier:
    cascade = cv2.CascadeClassifier(str(_CASCADE_PATH))
    if cascade.empty():
        raise ValueError(f"Failed to load Haar cascade from '{_CASCADE_PATH}'.")
    return cascade


def filter_eye_candidates(
    eyes: np.ndarray | list[tuple[int, int, int, int]],
) -> list[tuple[int, int, int, int]]:
    filtered: list[tuple[int, int, int, int]] = []

    for x, y, w, h in eyes:
        if w <= 0 or h <= 0:
            continue

        aspect_ratio = w / h
        if MIN_EYE_ASPECT_RATIO <= aspect_ratio <= MAX_EYE_ASPECT_RATIO:
            filtered.append((int(x), int(y), int(w), int(h)))

    return filtered


class EyeDetection(BaseOperator):
    def compute(self, image: np.ndarray) -> np.ndarray:
        scale_factor = float(self.params.get("scaleFactor", 1.2))
        min_neighbors = int(self.params.get("minNeighbors", 8))
        min_size = int(self.params.get("minSize", 24))
        thickness = int(self.params.get("thickness", 5))
        bgr_color = hex_to_bgr(self.params.get("rgbcolors_input", "#00ff00"))

        if scale_factor <= 1.0:
            raise ValueError(f"scaleFactor must be greater than 1.0, got {scale_factor}")
        if min_neighbors < 0:
            raise ValueError(f"minNeighbors must be >= 0, got {min_neighbors}")
        if min_size < 0:
            raise ValueError(f"minSize must be >= 0, got {min_size}")
        if thickness < 4 or thickness > 20:
            raise ValueError(f"thickness must be between 5 and 20, got {thickness}")

        gray = to_grayscale(image)
        if gray.dtype != np.uint8:
            gray = np.clip(gray, 0, 255).astype(np.uint8)
        gray = cv2.equalizeHist(gray)
        working_gray, resize_scale, min_size_tuple = resize_for_detection(gray, min_size)

        cascade = load_eye_cascade()
        eyes = cascade.detectMultiScale(
            working_gray,
            scaleFactor=scale_factor,
            minNeighbors=min_neighbors,
            minSize=min_size_tuple,
        )
        filtered_eyes = filter_eye_candidates(eyes)

        result, alpha_suffix = prepare_output(image)
        draw_color = (*bgr_color, *alpha_suffix)
        for x, y, w, h in filtered_eyes:
            if resize_scale < 1.0:
                x = int(round(x / resize_scale))
                y = int(round(y / resize_scale))
                w = int(round(w / resize_scale))
                h = int(round(h / resize_scale))
            cv2.rectangle(result, (x, y), (x + w, y + h), draw_color, thickness)

        return result

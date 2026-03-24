from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from app.operators.base import BaseOperator
from app.utils.color import hex_to_bgr

_CASCADE_PATH = Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml"
MAX_DETECTION_DIM = 720
MIN_FACE_ASPECT_RATIO = 0.75
MAX_FACE_ASPECT_RATIO = 1.35


def load_face_cascade() -> cv2.CascadeClassifier:
    cascade = cv2.CascadeClassifier(str(_CASCADE_PATH))
    if cascade.empty():
        raise ValueError(f"Failed to load Haar cascade from '{_CASCADE_PATH}'.")
    return cascade


def to_grayscale(image: np.ndarray) -> np.ndarray:
    if image.ndim == 2:
        return image
    if image.ndim == 3 and image.shape[2] == 1:
        return image[:, :, 0]
    if image.ndim == 3 and image.shape[2] == 3:
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    if image.ndim == 3 and image.shape[2] == 4:
        return cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
    raise ValueError(f"Unsupported image shape {image.shape}.")


def prepare_output(image: np.ndarray) -> tuple[np.ndarray, tuple[int, ...]]:
    if image.ndim == 2:
        return cv2.cvtColor(image, cv2.COLOR_GRAY2BGR), ()
    if image.ndim == 3 and image.shape[2] == 1:
        return cv2.cvtColor(image[:, :, 0], cv2.COLOR_GRAY2BGR), ()
    if image.ndim == 3 and image.shape[2] == 3:
        return image.copy(), ()
    if image.ndim == 3 and image.shape[2] == 4:
        return image.copy(), (255,)
    raise ValueError(f"Unsupported image shape {image.shape}.")


def resize_for_detection(gray: np.ndarray, min_size: int) -> tuple[np.ndarray, float, tuple[int, int]]:
    height, width = gray.shape[:2]
    if width <= 0 or height <= 0:
        raise ValueError(f"Invalid image dimensions {width}x{height}.")

    scale = min(MAX_DETECTION_DIM / max(height, width), 1.0)
    if scale == 1.0:
        return gray, 1.0, (min_size, min_size) if min_size > 0 else (0, 0)

    resized_width = max(1, int(round(width * scale)))
    resized_height = max(1, int(round(height * scale)))
    resized = cv2.resize(gray, (resized_width, resized_height), interpolation=cv2.INTER_AREA)
    scaled_min_size = max(1, int(round(min_size * scale))) if min_size > 0 else 0
    return resized, scale, ((scaled_min_size, scaled_min_size) if scaled_min_size > 0 else (0, 0))


def filter_face_candidates(
    faces: np.ndarray | list[tuple[int, int, int, int]],
) -> list[tuple[int, int, int, int]]:
    filtered: list[tuple[int, int, int, int]] = []

    for x, y, w, h in faces:
        if w <= 0 or h <= 0:
            continue

        aspect_ratio = w / h
        if MIN_FACE_ASPECT_RATIO <= aspect_ratio <= MAX_FACE_ASPECT_RATIO:
            filtered.append((int(x), int(y), int(w), int(h)))

    return filtered


class FaceDetection(BaseOperator):
    def compute(self, image: np.ndarray) -> np.ndarray:
        scale_factor = float(self.params.get("scaleFactor", 1.3))
        min_neighbors = int(self.params.get("minNeighbors", 6))
        min_size = int(self.params.get("minSize", 80))
        thickness = int(self.params.get("thickness", 2))
        bgr_color = hex_to_bgr(self.params.get("rgbcolors_input", "#00ff00"))

        if scale_factor <= 1.0:
            raise ValueError(f"scaleFactor must be greater than 1.0, got {scale_factor}")
        if min_neighbors < 0:
            raise ValueError(f"minNeighbors must be >= 0, got {min_neighbors}")
        if min_size < 0:
            raise ValueError(f"minSize must be >= 0, got {min_size}")
        if thickness < 1 or thickness > 20:
            raise ValueError(f"thickness must be between 1 and 20, got {thickness}")

        gray = to_grayscale(image)
        if gray.dtype != np.uint8:
            gray = np.clip(gray, 0, 255).astype(np.uint8)
        gray = cv2.equalizeHist(gray)
        working_gray, resize_scale, min_size_tuple = resize_for_detection(gray, min_size)

        cascade = load_face_cascade()
        faces = cascade.detectMultiScale(
            working_gray,
            scaleFactor=scale_factor,
            minNeighbors=min_neighbors,
            minSize=min_size_tuple,
        )
        filtered_faces = filter_face_candidates(faces)

        result, alpha_suffix = prepare_output(image)
        draw_color = (*bgr_color, *alpha_suffix)
        for x, y, w, h in filtered_faces:
            if resize_scale < 1.0:
                x = int(round(x / resize_scale))
                y = int(round(y / resize_scale))
                w = int(round(w / resize_scale))
                h = int(round(h / resize_scale))
            cv2.rectangle(result, (x, y), (x + w, y + h), draw_color, thickness)

        return result

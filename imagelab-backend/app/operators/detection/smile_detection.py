from pathlib import Path

import cv2
import numpy as np

from app.operators.base import BaseOperator
from app.operators.detection.common import prepare_output, resize_for_detection, to_grayscale
from app.utils.color import hex_to_bgr

_FACE_CASCADE_PATH = Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml"
_SMILE_CASCADE_PATH = Path(cv2.data.haarcascades) / "haarcascade_smile.xml"
MIN_FACE_ASPECT_RATIO = 0.75
MAX_FACE_ASPECT_RATIO = 1.35
MIN_SMILE_ASPECT_RATIO = 0.8
MAX_SMILE_ASPECT_RATIO = 4.5

FACE_SCALE_FACTOR = 1.2
FACE_MIN_NEIGHBORS = 6
FACE_MIN_SIZE = 80

LOWER_FACE_START_RATIO = 0.45
LOWER_FACE_END_RATIO = 0.9
MIN_SMILE_WIDTH_RATIO = 0.2
MAX_SMILE_WIDTH_RATIO = 0.85
MIN_SMILE_HEIGHT_RATIO = 0.08
MAX_SMILE_HEIGHT_RATIO = 0.45


def load_face_cascade() -> cv2.CascadeClassifier:
    cascade = cv2.CascadeClassifier(str(_FACE_CASCADE_PATH))
    if cascade.empty():
        raise ValueError(f"Failed to load Haar cascade from '{_FACE_CASCADE_PATH}'.")
    return cascade


def load_smile_cascade() -> cv2.CascadeClassifier:
    cascade = cv2.CascadeClassifier(str(_SMILE_CASCADE_PATH))
    if cascade.empty():
        raise ValueError(f"Failed to load Haar cascade from '{_SMILE_CASCADE_PATH}'.")
    return cascade


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


def filter_smile_candidates(
    smiles: np.ndarray | list[tuple[int, int, int, int]],
    face_width: int,
    face_height: int,
) -> list[tuple[int, int, int, int]]:
    filtered: list[tuple[int, int, int, int]] = []

    min_width = face_width * MIN_SMILE_WIDTH_RATIO
    max_width = face_width * MAX_SMILE_WIDTH_RATIO
    min_height = face_height * MIN_SMILE_HEIGHT_RATIO
    max_height = face_height * MAX_SMILE_HEIGHT_RATIO

    for x, y, w, h in smiles:
        if w <= 0 or h <= 0:
            continue

        aspect_ratio = w / h
        if not (MIN_SMILE_ASPECT_RATIO <= aspect_ratio <= MAX_SMILE_ASPECT_RATIO):
            continue
        if not (min_width <= w <= max_width):
            continue
        if not (min_height <= h <= max_height):
            continue

        filtered.append((int(x), int(y), int(w), int(h)))

    return filtered


def choose_best_smile(smiles: list[tuple[int, int, int, int]]) -> tuple[int, int, int, int] | None:
    if not smiles:
        return None
    return max(smiles, key=lambda smile: smile[2] * smile[3])


class SmileDetection(BaseOperator):
    def compute(self, image: np.ndarray) -> np.ndarray:
        scale_factor = float(self.params.get("scaleFactor", 1.6))
        min_neighbors = int(self.params.get("minNeighbors", 18))
        min_size = int(self.params.get("minSize", 24))
        thickness = int(self.params.get("thickness", 2))
        bgr_color = hex_to_bgr(self.params.get("rgbcolors_input", "#00ff00"))

        if scale_factor <= 1.0:
            raise ValueError(f"scaleFactor must be greater than 1.0, got {scale_factor}")
        if min_neighbors < 0:
            raise ValueError(f"minNeighbors must be >= 0, got {min_neighbors}")
        if min_size < 0:
            raise ValueError(f"minSize must be >= 0, got {min_size}")
        if thickness < 1 or thickness > 45:
            raise ValueError(f"thickness must be between 1 and 45, got {thickness}")

        gray = to_grayscale(image)
        if gray.dtype != np.uint8:
            gray = np.clip(gray, 0, 255).astype(np.uint8)
        gray = cv2.equalizeHist(gray)
        working_gray, resize_scale, _ = resize_for_detection(gray, FACE_MIN_SIZE)

        face_cascade = load_face_cascade()
        if resize_scale < 1.0:
            scaled_face_min_size = max(1, int(round(FACE_MIN_SIZE * resize_scale)))
            face_min_size_tuple = (scaled_face_min_size, scaled_face_min_size)
        else:
            face_min_size_tuple = (FACE_MIN_SIZE, FACE_MIN_SIZE)

        faces = face_cascade.detectMultiScale(
            working_gray,
            scaleFactor=FACE_SCALE_FACTOR,
            minNeighbors=FACE_MIN_NEIGHBORS,
            minSize=face_min_size_tuple,
        )
        filtered_faces = filter_face_candidates(faces)

        smile_cascade = load_smile_cascade()
        result, alpha_suffix = prepare_output(image)
        draw_color = (*bgr_color, *alpha_suffix)

        for face_x, face_y, face_w, face_h in filtered_faces:
            roi_y_start = face_y + int(round(face_h * LOWER_FACE_START_RATIO))
            roi_y_end = face_y + int(round(face_h * LOWER_FACE_END_RATIO))
            roi_y_end = min(roi_y_end, face_y + face_h)
            if roi_y_end <= roi_y_start:
                continue

            mouth_roi = working_gray[roi_y_start:roi_y_end, face_x : face_x + face_w]
            if mouth_roi.size == 0:
                continue

            scaled_smile_min_size = max(1, int(round(min_size * resize_scale))) if resize_scale < 1.0 else min_size

            smiles = smile_cascade.detectMultiScale(
                mouth_roi,
                scaleFactor=scale_factor,
                minNeighbors=min_neighbors,
                minSize=(scaled_smile_min_size, scaled_smile_min_size) if scaled_smile_min_size > 0 else (0, 0),
            )
            filtered_smiles = filter_smile_candidates(smiles, face_w, face_h)
            best_smile = choose_best_smile(filtered_smiles)
            if best_smile is None:
                continue

            smile_x, smile_y, smile_w, smile_h = best_smile
            absolute_x = face_x + smile_x
            absolute_y = roi_y_start + smile_y

            if resize_scale < 1.0:
                absolute_x = int(round(absolute_x / resize_scale))
                absolute_y = int(round(absolute_y / resize_scale))
                smile_w = int(round(smile_w / resize_scale))
                smile_h = int(round(smile_h / resize_scale))

            cv2.rectangle(
                result,
                (absolute_x, absolute_y),
                (absolute_x + smile_w, absolute_y + smile_h),
                draw_color,
                thickness,
            )

        return result

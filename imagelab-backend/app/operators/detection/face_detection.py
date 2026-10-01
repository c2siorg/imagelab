from functools import lru_cache

import cv2
import numpy as np

from app.operators.base import BaseOperator
from app.utils.color import hex_to_bgr


@lru_cache(maxsize=1)
def _get_face_cascade() -> cv2.CascadeClassifier:
    """Load and cache the Haar cascade classifier for frontal face detection."""
    cascade_path = cv2.data.haarcascades
    face_cascade_path = f"{cascade_path}haarcascade_frontalface_default.xml"
    cascade = cv2.CascadeClassifier(face_cascade_path)
    if cascade.empty():
        raise ValueError(f"Failed to load face cascade from {face_cascade_path}")
    return cascade


class FaceDetection(BaseOperator):
    """Detect frontal human faces using Haar cascades.

    Runs Haar cascade detection on a grayscale, histogram-equalized copy of the input.
    Bounding boxes are drawn on a copy of the original image to preserve source colors and dtype.
    If no faces are detected, returns the input image unchanged.
    """

    def __init__(self, params: dict):
        super().__init__(params)
        self.face_cascade = _get_face_cascade()

    def compute(self, image: np.ndarray) -> np.ndarray:
        # Extract parameters
        scale_factor = float(self.params.get("scaleFactor", 1.1))
        min_neighbors = int(self.params.get("minNeighbors", 5))
        min_size = self.params.get("minSize")
        min_width = int(self.params.get("minWidth", min_size if min_size is not None else 30))
        min_height = int(self.params.get("minHeight", min_size if min_size is not None else 30))
        box_color = hex_to_bgr(self.params.get("rgbcolors_input", "#00ff00"))
        thickness = int(self.params.get("thickness", 2))

        # Validate parameters (range-validated in the same style as filtering/contour_detection.py)
        if scale_factor < 1.01 or scale_factor > 2.0:
            raise ValueError(f"scaleFactor must be between 1.01 and 2.0, got {scale_factor}")
        if min_neighbors < 1 or min_neighbors > 20:
            raise ValueError(f"minNeighbors must be between 1 and 20, got {min_neighbors}")
        if min_width < 10 or min_width > 500:
            raise ValueError(f"minWidth must be between 10 and 500, got {min_width}")
        if min_height < 10 or min_height > 500:
            raise ValueError(f"minHeight must be between 10 and 500, got {min_height}")
        if thickness < 1 or thickness > 10:
            raise ValueError(f"thickness must be between 1 and 10, got {thickness}")

        # Ensure input shape is valid
        if not (len(image.shape) == 2 or (len(image.shape) == 3 and image.shape[2] in (1, 3, 4))):
            raise ValueError(f"Unsupported image shape {image.shape}.")

        if image.size == 0 or image.shape[0] == 0 or image.shape[1] == 0:
            return image.copy()

        # Normalize to uint8 for Haar cascade detection
        if image.dtype != np.uint8:
            if np.issubdtype(image.dtype, np.floating):
                norm_image = (image * 255.0 if image.max() <= 1.0 else image).clip(0, 255).astype(np.uint8)
            elif image.dtype == np.uint16:
                norm_image = (image >> 8).astype(np.uint8)
            else:
                norm_image = image.astype(np.uint8)
        else:
            norm_image = image.copy()

        # Build grayscale copy for detection
        if len(norm_image.shape) == 2:
            gray = norm_image
        elif len(norm_image.shape) == 3 and norm_image.shape[2] == 1:
            gray = norm_image[:, :, 0]
        elif len(norm_image.shape) == 3 and norm_image.shape[2] == 3:
            gray = cv2.cvtColor(norm_image, cv2.COLOR_BGR2GRAY)
        else:  # 4-channel BGRA
            gray = cv2.cvtColor(norm_image, cv2.COLOR_BGRA2GRAY)

        # Detection runs on a grayscale, histogram-equalized copy of the input
        equalized = cv2.equalizeHist(gray)

        # Detect faces
        faces = self.face_cascade.detectMultiScale(
            equalized,
            scaleFactor=scale_factor,
            minNeighbors=min_neighbors,
            minSize=(min_width, min_height),
        )

        # An image with no detections returns the input unchanged instead of raising
        if len(faces) == 0:
            return image.copy()

        # Detections found: draw bounding boxes on a copy of the original so source colors and dtype are preserved.
        # Single-channel/grayscale inputs are promoted to BGR so colored boxes can be rendered.
        if len(image.shape) == 2:
            canvas = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        elif len(image.shape) == 3 and image.shape[2] == 1:
            canvas = cv2.cvtColor(image[:, :, 0], cv2.COLOR_GRAY2BGR)
        else:
            canvas = image.copy()

        is_bgra = len(canvas.shape) == 3 and canvas.shape[2] == 4
        if np.issubdtype(canvas.dtype, np.floating):
            scale = 1.0 / 255.0 if image.max() <= 1.0 else 1.0
            color_vals = tuple(float(c) * scale for c in box_color)
            draw_color = (*color_vals, 1.0 if image.max() <= 1.0 else 255.0) if is_bgra else color_vals
        elif canvas.dtype == np.uint16:
            color_vals = tuple((int(c) << 8) | int(c) for c in box_color)
            draw_color = (*color_vals, 65535) if is_bgra else color_vals
        else:
            draw_color = (*box_color, 255) if is_bgra else box_color

        for x, y, w, h in faces:
            cv2.rectangle(canvas, (x, y), (x + w, y + h), draw_color, thickness)

        return canvas

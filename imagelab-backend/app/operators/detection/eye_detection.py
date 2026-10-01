import cv2
import numpy as np

from app.operators.base import BaseOperator
from app.utils.color import hex_to_bgr


class EyeDetection(BaseOperator):
    """Detect eyes using Haar cascades.

    Runs Haar cascade detection on a grayscale, histogram-equalized copy of the input.
    Bounding boxes are drawn on a copy of the original image to preserve source colors.
    If no eyes are detected, returns the input image unchanged.
    """

    def __init__(self, params: dict):
        super().__init__(params)

        # Load Haar cascade classifier once per operator instance
        cascade_path = cv2.data.haarcascades
        eye_cascade_path = f"{cascade_path}haarcascade_eye.xml"

        self.eye_cascade = cv2.CascadeClassifier(eye_cascade_path)

        if self.eye_cascade.empty():
            raise ValueError(f"Failed to load eye cascade from {eye_cascade_path}")

    def compute(self, image: np.ndarray) -> np.ndarray:
        # Extract parameters
        scale_factor = float(self.params.get("scaleFactor", 1.1))
        min_neighbors = int(self.params.get("minNeighbors", 5))
        min_size = self.params.get("minSize")
        min_width = int(self.params.get("minWidth", min_size if min_size is not None else 10))
        min_height = int(self.params.get("minHeight", min_size if min_size is not None else 10))
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

        # Detect eyes
        eyes = self.eye_cascade.detectMultiScale(
            equalized,
            scaleFactor=scale_factor,
            minNeighbors=min_neighbors,
            minSize=(min_width, min_height),
        )

        # An image with no detections returns the input unchanged instead of raising
        if len(eyes) == 0:
            return image.copy()

        # Detections found: draw bounding boxes on a copy of the original so source colors are preserved.
        # Single-channel/grayscale inputs are promoted to BGR so colored boxes can be rendered.
        if len(norm_image.shape) == 2:
            canvas = cv2.cvtColor(norm_image, cv2.COLOR_GRAY2BGR)
            draw_color = box_color
        elif len(norm_image.shape) == 3 and norm_image.shape[2] == 1:
            canvas = cv2.cvtColor(norm_image[:, :, 0], cv2.COLOR_GRAY2BGR)
            draw_color = box_color
        elif len(norm_image.shape) == 3 and norm_image.shape[2] == 3:
            canvas = norm_image.copy()
            draw_color = box_color
        else:  # 4-channel BGRA
            canvas = norm_image.copy()
            draw_color = (*box_color, 255)

        for x, y, w, h in eyes:
            cv2.rectangle(canvas, (x, y), (x + w, y + h), draw_color, thickness)

        return canvas

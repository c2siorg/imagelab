import cv2
import numpy as np

from app.operators.base import BaseOperator

MORPH_TYPES = {
    "OPEN": cv2.MORPH_OPEN,
    "CLOSE": cv2.MORPH_CLOSE,
    "GRADIENT": cv2.MORPH_GRADIENT,
    "TOPHAT": cv2.MORPH_TOPHAT,
    "BLACKHAT": cv2.MORPH_BLACKHAT,
}

NEEDS_RGB_CONVERSION = {"GRADIENT", "TOPHAT", "BLACKHAT"}


class Morphological(BaseOperator):
    def compute(self, image: np.ndarray) -> np.ndarray:
        morph_name = self.params.get("type", "TOPHAT")
        morph_type = MORPH_TYPES.get(morph_name, cv2.MORPH_TOPHAT)
        # Convert RGBA to RGB for certain morph types
        if morph_name in NEEDS_RGB_CONVERSION and len(image.shape) == 3 and image.shape[2] == 4:
            image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
        kernel = np.ones((5, 5), np.uint8)
        return cv2.morphologyEx(image, morph_type, kernel)

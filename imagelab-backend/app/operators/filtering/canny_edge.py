import cv2
import numpy as np

from app.operators.base import BaseOperator


class CannyEdge(BaseOperator):
    def compute(self, image: np.ndarray) -> np.ndarray:
        threshold1 = float(self.params.get("threshold1", 100))
        threshold2 = float(self.params.get("threshold2", 200))
        aperture_size = int(self.params.get("apertureSize", 3))

        threshold1 = max(0.0, min(255.0, threshold1))
        threshold2 = max(0.0, min(255.0, threshold2))

        if aperture_size not in (3, 5, 7):
            aperture_size = 3

        if len(image.shape) == 3 and image.shape[2] == 4:
            gray = cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
        elif len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        if gray.dtype != np.uint8:
            gray = np.clip(gray, 0, 255).astype(np.uint8)

        edges = cv2.Canny(gray, threshold1, threshold2, apertureSize=aperture_size)
        return cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)

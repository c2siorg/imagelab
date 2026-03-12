import cv2
import numpy as np

from app.operators.base import BaseOperator


class CannyEdge(BaseOperator):
    """Canny edge detection operator."""

    def compute(self, image: np.ndarray) -> np.ndarray:
        threshold1 = int(self.params.get("threshold1", 100))
        threshold2 = int(self.params.get("threshold2", 200))

        if threshold1 > threshold2:
            raise ValueError(f"threshold1 ({threshold1}) must be <= threshold2 ({threshold2})")

        # Convert to grayscale if needed
        if len(image.shape) == 3:
            if image.shape[2] == 4:
                gray = cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
            else:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        # Apply Canny edge detection
        edges = cv2.Canny(gray, threshold1, threshold2)

        return edges

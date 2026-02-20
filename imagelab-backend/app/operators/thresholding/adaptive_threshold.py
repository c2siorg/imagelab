import cv2
import numpy as np

from app.operators.base import BaseOperator


class AdaptiveThreshold(BaseOperator):
    def compute(self, image: np.ndarray) -> np.ndarray:
        max_value = float(self.params.get("maxValue", 0))
        # Convert to grayscale if not already
        if len(image.shape) == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return cv2.adaptiveThreshold(
            image,
            max_value,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            3,
            2,
        )

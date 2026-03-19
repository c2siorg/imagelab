import cv2
import numpy as np

from app.operators.base import BaseOperator


class OtsuThreshold(BaseOperator):
    def compute(self, image: np.ndarray) -> np.ndarray:
        max_value = float(self.params.get("maxValue", 255))
        # Convert to grayscale if not already
        if len(image.shape) == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, image = cv2.threshold(
            image,
            0,
            int(max_value),
            cv2.THRESH_BINARY + cv2.THRESH_OTSU,
        )
        return image

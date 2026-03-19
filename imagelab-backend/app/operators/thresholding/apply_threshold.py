import cv2
import numpy as np

from app.operators.base import BaseOperator


class ApplyThreshold(BaseOperator):
    def compute(self, image: np.ndarray) -> np.ndarray:
        max_value = float(self.params.get("maxValue", 255))
        threshold_value = float(self.params.get("thresholdValue", 0))
        max_value = max(0.0, min(255.0, max_value))
        threshold_value = max(0.0, min(255.0, threshold_value))
        _, dst = cv2.threshold(image, threshold_value, max_value, cv2.THRESH_BINARY)
        return dst

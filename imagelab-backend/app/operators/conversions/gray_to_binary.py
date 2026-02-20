import cv2
import numpy as np

from app.operators.base import BaseOperator


class GrayToBinary(BaseOperator):
    def compute(self, image: np.ndarray) -> np.ndarray:
        threshold_value = float(self.params.get("thresholdValue", 0))
        max_value = float(self.params.get("maxValue", 0))
        _, dst = cv2.threshold(image, threshold_value, max_value, cv2.THRESH_BINARY)
        return dst

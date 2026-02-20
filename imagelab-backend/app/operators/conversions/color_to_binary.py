import cv2
import numpy as np

from app.operators.base import BaseOperator

THRESHOLD_TYPES = {
    "threshold_binary": cv2.THRESH_BINARY,
    "threshold_binary_inv": cv2.THRESH_BINARY_INV,
}


class ColorToBinary(BaseOperator):
    def compute(self, image: np.ndarray) -> np.ndarray:
        threshold_type_name = self.params.get("thresholdType", "threshold_binary")
        threshold_type = THRESHOLD_TYPES.get(threshold_type_name, cv2.THRESH_BINARY)
        threshold_value = float(self.params.get("thresholdValue", 0))
        max_value = float(self.params.get("maxValue", 0))
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, dst = cv2.threshold(gray, threshold_value, max_value, threshold_type)
        return dst

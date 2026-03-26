import cv2
import numpy as np

from app.operators.base import BaseOperator

THRESHOLD_TYPES = {
    "threshold_binary": cv2.THRESH_BINARY,
    "threshold_binary_inv": cv2.THRESH_BINARY_INV,
}

_DEFAULTS = {
    "thresholdType": "threshold_binary",
    "thresholdValue": 0,
    "maxValue": 255,
}


class ColorToBinary(BaseOperator):
    def compute(self, image: np.ndarray) -> np.ndarray:
        threshold_type_name = self.params.get("thresholdType", _DEFAULTS["thresholdType"])
        threshold_type = THRESHOLD_TYPES.get(threshold_type_name, cv2.THRESH_BINARY)
        threshold_value = float(self.params.get("thresholdValue", _DEFAULTS["thresholdValue"]))
        max_value = float(self.params.get("maxValue", _DEFAULTS["maxValue"]))
        if len(image.shape) == 3 and image.shape[2] == 4:
            gray = cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
        else:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, dst = cv2.threshold(gray, threshold_value, max_value, threshold_type)
        return dst

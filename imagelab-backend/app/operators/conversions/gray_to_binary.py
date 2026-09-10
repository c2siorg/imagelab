import cv2
import numpy as np

from app.operators.base import BaseOperator


class GrayToBinary(BaseOperator):
    def compute(self, image: np.ndarray) -> np.ndarray:
        threshold_value = float(self.params.get("thresholdValue", 127))
        max_value = float(self.params.get("maxValue", 255))

        # Convert color images to grayscale before thresholding.
        # Passing a BGR or BGRA image directly to cv2.threshold produces a
        # multi-channel binary output instead of a proper grayscale binary image.
        if image.ndim == 3:
            if image.shape[2] == 4:
                image = cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
            else:
                image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        _, dst = cv2.threshold(image, threshold_value, max_value, cv2.THRESH_BINARY)
        return dst

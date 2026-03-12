import cv2
import numpy as np

from app.operators.base import BaseOperator


class SobelDerivative(BaseOperator):
    def compute(self, image: np.ndarray) -> np.ndarray:
        """Apply the Sobel derivative operator.

        Returns a uint8 image with values in [0, 255].
        """
        direction = self.params.get("type", "HORIZONTAL")
        ddepth = int(self.params.get("ddepth", 0))
        if ddepth == 0:
            ddepth = cv2.CV_64F

        if direction == "HORIZONTAL":
            result = cv2.Sobel(image, ddepth, 1, 0)
        elif direction == "VERTICAL":
            result = cv2.Sobel(image, ddepth, 0, 1)
        else:
            sobel_x = cv2.Sobel(image, ddepth, 1, 0)
            sobel_y = cv2.Sobel(image, ddepth, 0, 1)
            result = np.hypot(sobel_x, sobel_y)

        return cv2.convertScaleAbs(result)

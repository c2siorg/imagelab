import cv2
import numpy as np

from app.operators.base import BaseOperator
from app.operators.sobel_derivatives.sobel_derivative import _to_grayscale


class ScharrDerivative(BaseOperator):
    def compute(self, image: np.ndarray) -> np.ndarray:
        """Apply the Scharr derivative operator.

        Returns a uint8 grayscale image with values in [0, 255].
        BGRA images are converted to grayscale before applying Scharr.
        """
        direction = self.params.get("type", "HORIZONTAL")
        ddepth = int(self.params.get("ddepth", 0))
        if ddepth == 0:
            ddepth = cv2.CV_64F

        gray = _to_grayscale(image)

        result = cv2.Scharr(gray, ddepth, 1, 0) if direction == "HORIZONTAL" else cv2.Scharr(gray, ddepth, 0, 1)

        return cv2.convertScaleAbs(result)

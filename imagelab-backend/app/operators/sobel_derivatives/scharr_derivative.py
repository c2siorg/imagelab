import cv2
import numpy as np

from app.operators.base import BaseOperator


class ScharrDerivative(BaseOperator):
    def compute(self, image: np.ndarray) -> np.ndarray:
        """Apply the Scharr derivative operator.

        Returns a uint8 image with values in [0, 255].
        """
        direction = self.params.get("type", "HORIZONTAL")
        ddepth = int(self.params.get("ddepth", 0))
        if ddepth == 0:
            ddepth = cv2.CV_64F

        result = cv2.Scharr(image, ddepth, 1, 0) if direction == "HORIZONTAL" else cv2.Scharr(image, ddepth, 0, 1)

        return cv2.convertScaleAbs(result)

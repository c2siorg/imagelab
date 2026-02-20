import cv2
import numpy as np

from app.operators.base import BaseOperator


class ScharrDerivative(BaseOperator):
    def compute(self, image: np.ndarray) -> np.ndarray:
        direction = self.params.get("type", "HORIZONTAL")
        ddepth = int(self.params.get("ddepth", 0))
        if ddepth == 0:
            ddepth = cv2.CV_64F

        if direction == "HORIZONTAL":
            return cv2.Scharr(image, ddepth, 1, 0)
        else:
            return cv2.Scharr(image, ddepth, 0, 1)

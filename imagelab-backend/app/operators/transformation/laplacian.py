import cv2
import numpy as np

from app.operators.base import BaseOperator


class Laplacian(BaseOperator):
    def compute(self, image: np.ndarray) -> np.ndarray:
        ddepth = int(self.params.get("ddepth", 0))
        if ddepth == 0:
            ddepth = cv2.CV_64F

        laplacian = cv2.Laplacian(image, ddepth)
        return np.uint8(np.absolute(laplacian))

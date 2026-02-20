import cv2
import numpy as np

from app.operators.base import BaseOperator


class RotateImage(BaseOperator):
    def compute(self, image: np.ndarray) -> np.ndarray:
        angle = float(self.params.get("angle", 90))
        scale = float(self.params.get("scale", 1))
        rows, cols = image.shape[:2]
        center = (cols / 2, rows / 2)
        M = cv2.getRotationMatrix2D(center, angle, scale)
        return cv2.warpAffine(image, M, (cols, rows))

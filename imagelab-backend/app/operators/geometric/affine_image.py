import cv2
import numpy as np

from app.operators.base import BaseOperator


class AffineImage(BaseOperator):
    def compute(self, image: np.ndarray) -> np.ndarray:
        rows, cols = image.shape[:2]
        M = np.float64([[1, 0, 50], [0, 1, 100]])
        return cv2.warpAffine(image, M, (cols, rows))

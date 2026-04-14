import cv2
import numpy as np

from app.operators.base import BaseOperator


class AffineImage(BaseOperator):
    def compute(self, image: np.ndarray) -> np.ndarray:
        rows, cols = image.shape[:2]
        tx = float(self.params.get("tx", 50))
        ty = float(self.params.get("ty", 100))
        M = np.float64([[1, 0, tx], [0, 1, ty]])
        return cv2.warpAffine(image, M, (cols, rows))

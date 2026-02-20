import cv2
import numpy as np

from app.operators.base import BaseOperator


class ScaleImage(BaseOperator):
    def compute(self, image: np.ndarray) -> np.ndarray:
        fx = float(self.params.get("fx", 1))
        fy = float(self.params.get("fy", 1))
        rows, cols = image.shape[:2]
        new_size = (int(cols * fx), int(rows * fy))
        return cv2.resize(image, new_size, fx=fx, fy=fy, interpolation=cv2.INTER_AREA)

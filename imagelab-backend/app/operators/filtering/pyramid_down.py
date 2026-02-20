import cv2
import numpy as np

from app.operators.base import BaseOperator


class PyramidDown(BaseOperator):
    def compute(self, image: np.ndarray) -> np.ndarray:
        return cv2.pyrDown(image)

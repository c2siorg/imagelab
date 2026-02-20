import cv2
import numpy as np

from app.operators.base import BaseOperator


class GrayImage(BaseOperator):
    def compute(self, image: np.ndarray) -> np.ndarray:
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

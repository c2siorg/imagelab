import cv2
import numpy as np

from app.operators.base import BaseOperator


class GaussianBlur(BaseOperator):
    def compute(self, image: np.ndarray) -> np.ndarray:
        width_size = int(self.params.get("widthSize", 1))
        height_size = int(self.params.get("heightSize", 1))
        # Ensure kernel sizes are odd
        if width_size % 2 == 0:
            width_size += 1
        if height_size % 2 == 0:
            height_size += 1
        return cv2.GaussianBlur(image, (width_size, height_size), 0)

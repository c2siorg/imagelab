import cv2
import numpy as np

from app.operators.base import BaseOperator
from app.operators.blurring.validation import validate_positive_odd_kernel_size


class GaussianBlur(BaseOperator):
    def compute(self, image: np.ndarray) -> np.ndarray:
        width_size = int(self.params.get("widthSize", 1))
        height_size = int(self.params.get("heightSize", 1))

        validate_positive_odd_kernel_size(width_size, "widthSize")
        validate_positive_odd_kernel_size(height_size, "heightSize")

        return cv2.GaussianBlur(image, (width_size, height_size), 0)

import cv2
import numpy as np

from app.operators.base import BaseOperator
from app.operators.blurring.validation import validate_positive_kernel_dim


class Blur(BaseOperator):
    def compute(self, image: np.ndarray) -> np.ndarray:
        width_size = int(self.params.get("widthSize", 3))
        height_size = int(self.params.get("heightSize", 3))
        point_x = int(self.params.get("pointX", -1))
        point_y = int(self.params.get("pointY", -1))

        validate_positive_kernel_dim(width_size, "widthSize")
        validate_positive_kernel_dim(height_size, "heightSize")

        return cv2.blur(
            image,
            (width_size, height_size),  # OpenCV ksize convention: (width, height)
            anchor=(point_x, point_y),
            borderType=cv2.BORDER_DEFAULT,
        )

import cv2
import numpy as np

from app.operators.base import BaseOperator
from app.operators.blurring.validation import validate_median_kernel_size


class MedianBlur(BaseOperator):
    def compute(self, image: np.ndarray) -> np.ndarray:
        kernel_size = int(self.params.get("kernelSize", 5))

        validate_median_kernel_size(kernel_size, "kernelSize")

        return cv2.medianBlur(image, kernel_size)

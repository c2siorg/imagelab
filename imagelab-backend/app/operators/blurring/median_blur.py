import cv2
import numpy as np

from app.operators.base import BaseOperator


class MedianBlur(BaseOperator):
    def compute(self, image: np.ndarray) -> np.ndarray:
        kernel_size = int(self.params.get("kernelSize", 5))
        # Ensure kernel size is odd
        if kernel_size % 2 == 0:
            kernel_size += 1
        return cv2.medianBlur(image, kernel_size)

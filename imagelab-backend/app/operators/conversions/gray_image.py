import cv2
import numpy as np

from app.operators.base import BaseOperator


class GrayImage(BaseOperator):
    def compute(self, image: np.ndarray) -> np.ndarray:
        if image.ndim == 2:
            return image

        if image.ndim == 3:
            channels = image.shape[2]
            if channels == 1:
                return image[:, :, 0]
            if channels == 3:
                return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            if channels == 4:
                return cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)

        raise ValueError("GrayImage expects a 2D grayscale image or a 3D image with 1, 3, or 4 channels")

import math

import cv2
import numpy as np

from app.operators.base import BaseOperator


class RotateImage(BaseOperator):
    def compute(self, image: np.ndarray) -> np.ndarray:
        angle = float(self.params.get("angle", 90))
        scale = float(self.params.get("scale", 1))

        if not math.isfinite(scale):
            raise ValueError(f"scale must be a finite number, got {scale}")
        if scale <= 0:
            raise ValueError(f"scale must be greater than 0, got {scale}")

        rows, cols = image.shape[:2]
        center = (cols / 2, rows / 2)
        M = cv2.getRotationMatrix2D(center, angle, scale)
        return cv2.warpAffine(image, M, (cols, rows))

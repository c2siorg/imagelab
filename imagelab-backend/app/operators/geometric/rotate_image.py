import cv2
import numpy as np

from app.operators.base import BaseOperator


class RotateImage(BaseOperator):
    def compute(self, image: np.ndarray) -> np.ndarray:
        angle = float(self.params.get("angle", 90))
        scale = float(self.params.get("scale", 1))

        if scale <= 0:
            raise ValueError(
                f"RotateImage: scale must be a positive number, got {scale}. "
                "Use a value greater than 0 (e.g. 1.0 for original size, 0.5 to shrink, 2.0 to enlarge)."
            )

        rows, cols = image.shape[:2]
        center = (cols / 2, rows / 2)
        M = cv2.getRotationMatrix2D(center, angle, scale)
        return cv2.warpAffine(image, M, (cols, rows))

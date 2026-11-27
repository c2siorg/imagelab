import cv2
import numpy as np

from app.operators.base import BaseOperator
from app.utils.image import check_output_memory


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
        center = ((cols - 1) / 2.0, (rows - 1) / 2.0)
        M = cv2.getRotationMatrix2D(center, angle, scale)
        cos = abs(M[0, 0])
        sin = abs(M[0, 1])
        new_w = max(1, int(round((rows * sin) + (cols * cos))))
        new_h = max(1, int(round((rows * cos) + (cols * sin))))
        check_output_memory(image, new_w, new_h)
        M[0, 2] += ((new_w - 1) / 2.0) - center[0]
        M[1, 2] += ((new_h - 1) / 2.0) - center[1]
        return cv2.warpAffine(image, M, (new_w, new_h))

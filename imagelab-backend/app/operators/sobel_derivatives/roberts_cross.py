import cv2
import numpy as np

from app.operators.base import BaseOperator

# Roberts Cross kernels — 2x2 diagonal gradient operators
_KERNEL_X = np.array([[1, 0], [0, -1]], dtype=np.float64)
_KERNEL_Y = np.array([[0, 1], [-1, 0]], dtype=np.float64)


class RobertsCross(BaseOperator):
    """Applies the Roberts Cross operator to detect edges using diagonal gradients."""

    def compute(self, image: np.ndarray) -> np.ndarray:
        if image.dtype != np.uint8:
            raise ValueError(f"RobertsCross expects a uint8 image, got dtype={image.dtype}.")
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image

        grad_x = cv2.filter2D(gray, cv2.CV_64F, _KERNEL_X)
        grad_y = cv2.filter2D(gray, cv2.CV_64F, _KERNEL_Y)

        magnitude = np.sqrt(grad_x**2 + grad_y**2)
        return np.clip(magnitude, 0, 255).astype(np.uint8)

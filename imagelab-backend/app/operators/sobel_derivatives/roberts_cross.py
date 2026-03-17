import cv2
import numpy as np

from app.operators.base import BaseOperator

# Roberts Cross kernels — 2x2 diagonal gradient operators
_KERNEL_X = np.array([[1, 0], [0, -1]], dtype=np.float64)
_KERNEL_Y = np.array([[0, 1], [-1, 0]], dtype=np.float64)


class RobertsCross(BaseOperator):
    """Applies the Roberts Cross operator to detect edges using diagonal gradients."""

    def compute(self, image: np.ndarray) -> np.ndarray:
        """Apply the Roberts Cross edge-detection operator.

        Args:
            image: uint8 ndarray of shape (H, W), (H, W, 1), (H, W, 3), or (H, W, 4).
                   Colour images are converted to grayscale before processing.
                   Non-uint8 images are normalised to uint8 before processing.

        Returns:
            uint8 ndarray of shape (H, W) containing gradient magnitudes
            clipped to [0, 255].
        """
        if image.dtype != np.uint8:
            norm = cv2.normalize(image, None, 0, 255, cv2.NORM_MINMAX)
            image = norm.astype(np.uint8)

        if image.ndim == 3:
            c = image.shape[2]
            if c == 1:
                gray = image[:, :, 0]
            elif c == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            elif c == 4:
                gray = cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
            else:
                raise ValueError(f"RobertsCross: unsupported channel count {c}.")
        else:
            gray = image

        grad_x = cv2.filter2D(gray, cv2.CV_64F, _KERNEL_X, anchor=(0, 0))
        grad_y = cv2.filter2D(gray, cv2.CV_64F, _KERNEL_Y, anchor=(0, 0))

        magnitude = np.sqrt(grad_x**2 + grad_y**2)
        return np.clip(magnitude, 0, 255).astype(np.uint8)

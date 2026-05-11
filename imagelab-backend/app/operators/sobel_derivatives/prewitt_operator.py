import cv2
import numpy as np

from app.operators.base import BaseOperator

_KERNEL_X = np.array([[-1, 0, 1], [-1, 0, 1], [-1, 0, 1]], dtype=np.float64)
_KERNEL_X.flags.writeable = False

_KERNEL_Y = np.array([[-1, -1, -1], [0, 0, 0], [1, 1, 1]], dtype=np.float64)
_KERNEL_Y.flags.writeable = False


class PrewittOperator(BaseOperator):
    """Applies the Prewitt operator to detect edges using horizontal and vertical gradient kernels.

    Note:
        Colour images are expected in BGR channel order (OpenCV convention).
        Grayscale images must be 2-D arrays of dtype uint8.
    """

    def compute(self, image: np.ndarray) -> np.ndarray:
        """Compute the Prewitt gradient magnitude.

        Args:
            image: uint8 ndarray of shape (H, W), (H, W, 1), (H, W, 3), or (H, W, 4)
                   in BGR channel order.

        Returns:
            uint8 ndarray of shape (H, W) containing gradient magnitudes
            clipped to [0, 255].

        Raises:
            ValueError: If ``image.dtype`` is not ``np.uint8``.
        """
        if image.dtype != np.uint8:
            raise ValueError(f"PrewittOperator expects a uint8 image, got dtype={image.dtype}.")

        if image.ndim == 2:
            gray = image
        elif image.ndim == 3:
            channels = image.shape[2]
            if channels == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            elif channels == 4:
                gray = cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
            elif channels == 1:
                gray = image[:, :, 0]
            else:
                raise ValueError(f"PrewittOperator expects 1, 3, or 4 channels, got shape={image.shape}.")
        else:
            raise ValueError(f"PrewittOperator expects a 2-D or 3-D array, got ndim={image.ndim}.")

        grad_x = cv2.filter2D(gray, cv2.CV_64F, _KERNEL_X)
        grad_y = cv2.filter2D(gray, cv2.CV_64F, _KERNEL_Y)

        magnitude = np.hypot(grad_x, grad_y)
        return np.minimum(magnitude, 255).astype(np.uint8)

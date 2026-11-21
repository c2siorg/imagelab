import math
from typing import Any

import cv2
import numpy as np

from app.operators.base import BaseOperator


def _safe_float(val: Any, default: float = 0.0) -> float:
    try:
        f = float(val)
        return default if math.isnan(f) or math.isinf(f) else f
    except (TypeError, ValueError):
        return default


def _safe_int(val: Any, default: int = 0) -> int:
    try:
        return int(val)
    except (TypeError, ValueError):
        return default


class MotionBlur(BaseOperator):
    """Applies directional motion blur to simulate linear camera motion or object velocity.

    Constructs a directional Point Spread Function (PSF) linear convolution kernel
    at the specified angle and convolves the image using cv2.filter2D.
    """

    def compute(self, image: np.ndarray) -> np.ndarray:
        if image is None or not isinstance(image, np.ndarray) or image.size == 0:
            raise ValueError("MotionBlur received an invalid or empty image.")

        if not (image.ndim == 2 or (image.ndim == 3 and image.shape[2] in (1, 3, 4))):
            raise ValueError(
                f"MotionBlur expects a 2-D or 3-D image with 1, 3, or 4 channels, got shape {image.shape}."
            )

        if image.dtype != np.uint8:
            raise ValueError(f"MotionBlur expects a uint8 image, got dtype={image.dtype}.")

        kernel_size = _safe_int(self.params.get("kernel_size", 15), 15)
        kernel_size = max(3, min(61, kernel_size))
        if kernel_size % 2 == 0:
            kernel_size += 1

        angle = _safe_float(self.params.get("angle", 0.0), 0.0) % 360.0

        # Construct directional linear convolution kernel
        k = kernel_size
        kernel = np.zeros((k, k), dtype=np.float32)
        kernel[k // 2, :] = 1.0

        if angle != 0.0:
            center = (k - 1) / 2.0
            rot_mat = cv2.getRotationMatrix2D((center, center), angle, 1.0)
            kernel = cv2.warpAffine(kernel, rot_mat, (k, k))

        kernel_sum = float(np.sum(kernel))
        if kernel_sum > 0:
            kernel /= kernel_sum
        else:
            kernel[k // 2, k // 2] = 1.0

        if image.ndim == 2:
            return cv2.filter2D(image, -1, kernel)
        elif image.ndim == 3 and image.shape[2] == 1:
            filtered = cv2.filter2D(image[:, :, 0], -1, kernel)
            return filtered[:, :, np.newaxis]
        elif image.ndim == 3 and image.shape[2] == 4:
            bgr = cv2.filter2D(image[:, :, :3], -1, kernel)
            alpha = image[:, :, 3]
            return np.dstack((bgr, alpha))
        else:
            return cv2.filter2D(image, -1, kernel)

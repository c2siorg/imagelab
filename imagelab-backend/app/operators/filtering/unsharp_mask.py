import cv2
import numpy as np

from app.operators.base import BaseOperator


def _safe_int(val: object, default: int) -> int:
    try:
        return int(float(str(val).strip()))
    except (TypeError, ValueError):
        return default


def _safe_float(val: object, default: float) -> float:
    try:
        return float(str(val).strip())
    except (TypeError, ValueError):
        return default


class UnsharpMask(BaseOperator):
    """Sharpens an image using the classic Unsharp Masking technique.

    Subtracts a low-pass Gaussian blurred version from the original image to isolate
    high-frequency edge details, applies an optional noise threshold gate, and adds
    scaled edge details back to the original image.
    """

    def compute(self, image: np.ndarray) -> np.ndarray:
        if image is None or not isinstance(image, np.ndarray) or image.size == 0:
            raise ValueError("UnsharpMask received an invalid or empty image.")

        if not (image.ndim == 2 or (image.ndim == 3 and image.shape[2] in (1, 3, 4))):
            raise ValueError(
                f"UnsharpMask expects a 2-D or 3-D image with 1, 3, or 4 channels, got shape {image.shape}."
            )

        if image.dtype != np.uint8:
            raise ValueError(f"UnsharpMask expects a uint8 image, got dtype={image.dtype}.")

        kernel_size = _safe_int(self.params.get("kernel_size", 5), 5)
        kernel_size = max(3, min(31, kernel_size))
        if kernel_size % 2 == 0:
            kernel_size += 1
            if kernel_size > 31:
                kernel_size = 31

        sigma = max(0.1, min(10.0, _safe_float(self.params.get("sigma", 1.0), 1.0)))
        amount = max(0.1, min(5.0, _safe_float(self.params.get("amount", 1.5), 1.5)))
        threshold = max(0, min(50, _safe_int(self.params.get("threshold", 0), 0)))

        if image.ndim == 2:
            src = image
            blurred = cv2.GaussianBlur(src, (kernel_size, kernel_size), sigma)
            diff = src.astype(np.float32) - blurred.astype(np.float32)
            if threshold > 0:
                diff = np.where(np.abs(diff) < threshold, 0.0, diff)
            return np.clip(src.astype(np.float32) + amount * diff, 0, 255).astype(np.uint8)

        elif image.ndim == 3 and image.shape[2] == 1:
            src = image[:, :, 0]
            blurred = cv2.GaussianBlur(src, (kernel_size, kernel_size), sigma)
            diff = src.astype(np.float32) - blurred.astype(np.float32)
            if threshold > 0:
                diff = np.where(np.abs(diff) < threshold, 0.0, diff)
            res = np.clip(src.astype(np.float32) + amount * diff, 0, 255).astype(np.uint8)
            return res[:, :, np.newaxis]

        elif image.ndim == 3 and image.shape[2] == 4:
            src = image[:, :, :3]
            alpha = image[:, :, 3]
            blurred = cv2.GaussianBlur(src, (kernel_size, kernel_size), sigma)
            diff = src.astype(np.float32) - blurred.astype(np.float32)
            if threshold > 0:
                diff = np.where(np.abs(diff) < threshold, 0.0, diff)
            res = np.clip(src.astype(np.float32) + amount * diff, 0, 255).astype(np.uint8)
            return np.dstack((res, alpha))

        else:
            src = image
            blurred = cv2.GaussianBlur(src, (kernel_size, kernel_size), sigma)
            diff = src.astype(np.float32) - blurred.astype(np.float32)
            if threshold > 0:
                diff = np.where(np.abs(diff) < threshold, 0.0, diff)
            return np.clip(src.astype(np.float32) + amount * diff, 0, 255).astype(np.uint8)

import cv2
import numpy as np

from app.operators.base import BaseOperator


class HistogramEqualization(BaseOperator):
    """Histogram equalization operator for contrast enhancement.

    Supports grayscale (H,W), BGR (H,W,3), and BGRA (H,W,4) uint8 images.
    """

    def compute(self, image: np.ndarray) -> np.ndarray:
        if image.dtype != np.uint8:
            raise ValueError(f"HistogramEqualization requires uint8 input, got {image.dtype}")

        if len(image.shape) == 2:
            # Grayscale image
            return cv2.equalizeHist(image)
        elif len(image.shape) == 3:
            if image.shape[2] == 3:
                # Color image - equalize on V channel of HSV
                hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
                hsv[:, :, 2] = cv2.equalizeHist(hsv[:, :, 2])
                return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
            elif image.shape[2] == 4:
                # BGRA image - preserve alpha channel
                alpha = image[:, :, 3]
                bgr = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
                hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
                hsv[:, :, 2] = cv2.equalizeHist(hsv[:, :, 2])
                bgr_result = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
                return cv2.merge([bgr_result[:, :, 0], bgr_result[:, :, 1], bgr_result[:, :, 2], alpha])

        raise ValueError(
            f"Unsupported image shape: {image.shape}. Expected grayscale (H,W), BGR (H,W,3), or BGRA (H,W,4)."
        )

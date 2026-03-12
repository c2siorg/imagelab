import cv2
import numpy as np

from app.operators.base import BaseOperator


class HistogramEqualization(BaseOperator):
    """
    Applies Histogram Equalization to an image.

    For color images (BGR), equalization is performed on the Y-channel of the
    YCrCb color space to avoid shifting hue or saturation.
    For BGRA images, alpha is preserved.
    For grayscale images, equalization is applied directly.
    """

    def compute(self, image: np.ndarray) -> np.ndarray:
        """
        Apply Histogram Equalization to the input image.

        Args:
            image: A uint8 NumPy array of shape (H, W), (H, W, 3) or (H, W, 4).

        Returns:
            A contrast-enhanced uint8 image of the same shape and dtype.

        Raises:
            ValueError: If the image is None, not uint8, or has unsupported shape.
        """
        if image is None:
            raise ValueError("Input image cannot be None")
        if image.dtype != np.uint8:
            raise ValueError(
                f"Histogram Equalization requires a uint8 image, but got dtype={image.dtype}."
            )

        if len(image.shape) == 2:
            return cv2.equalizeHist(image)
        elif len(image.shape) == 3:
            if image.shape[2] == 1:
                return cv2.equalizeHist(image[:, :, 0])
            elif image.shape[2] == 3:
                return self._apply_to_bgr(image)
            elif image.shape[2] == 4:
                # BGRA — apply to BGR, preserve alpha
                bgr = image[:, :, :3]
                alpha = image[:, :, 3]
                result_bgr = self._apply_to_bgr(bgr)
                return np.dstack([result_bgr, alpha])
            else:
                raise ValueError(f"Unsupported number of channels: {image.shape[2]}")
        else:
            raise ValueError(f"Unsupported image shape: {image.shape}")

    def _apply_to_bgr(self, image: np.ndarray) -> np.ndarray:
        # Step 1: BGR -> YCrCb
        ycrcb = cv2.cvtColor(image, cv2.COLOR_BGR2YCrCb)
        y, cr, cb = cv2.split(ycrcb)

        # Step 2: Apply to 'Y' channel
        y_equalized = cv2.equalizeHist(y)

        # Step 3: Merge back and BGR
        equalized_ycrcb = cv2.merge((y_equalized, cr, cb))
        return cv2.cvtColor(equalized_ycrcb, cv2.COLOR_YCrCb2BGR)

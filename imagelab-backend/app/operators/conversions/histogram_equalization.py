import cv2
import numpy as np

from app.operators.base import BaseOperator


class HistogramEqualization(BaseOperator):
    """
    Enhances image contrast using histogram equalization.
    Works for both grayscale and color images.
    No parameters required.
    """

    def compute(self, image: np.ndarray) -> np.ndarray:

        if image is None:
            return image

        # Grayscale image
        if len(image.shape) == 2:
            return cv2.equalizeHist(image)

        # Color image (BGR)
        if len(image.shape) == 3 and image.shape[2] == 3:
            # Convert to YCrCb to preserve color fidelity
            ycrcb = cv2.cvtColor(image, cv2.COLOR_BGR2YCrCb)

            # Equalize only the luminance channel
            ycrcb[:, :, 0] = cv2.equalizeHist(ycrcb[:, :, 0])

            # Convert back to BGR
            return cv2.cvtColor(ycrcb, cv2.COLOR_YCrCb2BGR)

        return image

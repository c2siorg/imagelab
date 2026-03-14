import cv2
import numpy as np

from app.operators.base import BaseOperator


class CannyEdge(BaseOperator):
    """
    Applies the Canny multi-stage edge detection algorithm.

    Automatically converts colour images to grayscale before detection.
    The result is a single-channel binary edge map (uint8, values 0 or 255).

    Parameters
    ----------
    threshold1 : int | float
        First (lower) hysteresis threshold. Default **100**.
    threshold2 : int | float
        Second (upper) hysteresis threshold. Default **200**.
    """

    def compute(self, image: np.ndarray) -> np.ndarray:
        threshold1 = float(self.params.get("threshold1", 100))
        threshold2 = float(self.params.get("threshold2", 200))

        # Guarantee a single-channel input for Canny
        if image.ndim == 3:
            if image.shape[2] == 4:
                gray = cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
            else:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        return cv2.Canny(gray, threshold1, threshold2)

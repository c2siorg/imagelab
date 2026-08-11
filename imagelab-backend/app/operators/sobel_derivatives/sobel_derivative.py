import cv2
import numpy as np

from app.operators.base import BaseOperator


def _to_grayscale(image: np.ndarray) -> np.ndarray:
    """Convert image to grayscale, handling BGRA, BGR, and already-grayscale inputs."""
    if image.ndim == 2:
        return image
    if image.shape[2] == 4:
        return cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


class SobelDerivative(BaseOperator):
    def compute(self, image: np.ndarray) -> np.ndarray:
        """Apply the Sobel derivative operator.

        Returns a uint8 grayscale image with values in [0, 255].
        BGRA images are converted to grayscale before applying Sobel.
        """
        direction = self.params.get("type", "HORIZONTAL")
        ddepth = int(self.params.get("ddepth", 0))
        if ddepth == 0:
            ddepth = cv2.CV_64F

        gray = _to_grayscale(image)

        if direction == "HORIZONTAL":
            result = cv2.Sobel(gray, ddepth, 1, 0)
        elif direction == "VERTICAL":
            result = cv2.Sobel(gray, ddepth, 0, 1)
        else:
            sobel_x = cv2.Sobel(gray, ddepth, 1, 0)
            sobel_y = cv2.Sobel(gray, ddepth, 0, 1)
            result = np.hypot(sobel_x, sobel_y)

        return cv2.convertScaleAbs(result)

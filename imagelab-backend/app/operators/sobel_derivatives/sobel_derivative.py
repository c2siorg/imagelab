import cv2
import numpy as np

from app.operators.base import BaseOperator


def _to_grayscale(image: np.ndarray) -> np.ndarray:
    """Convert image to grayscale, handling BGRA, BGR, and already-grayscale inputs.

    Supports:
        - 2-D grayscale arrays: (H, W)
        - 3-D single-channel arrays: (H, W, 1) -> squeezed to (H, W)
        - 3-D BGR arrays: (H, W, 3) -> converted via cv2.COLOR_BGR2GRAY
        - 3-D BGRA arrays: (H, W, 4) -> converted via cv2.COLOR_BGRA2GRAY
    """
    if image is None or not isinstance(image, np.ndarray) or image.size == 0:
        raise ValueError("Sobel derivative operator received an invalid or empty image.")

    if image.dtype != np.uint8:
        raise ValueError(f"Sobel derivative operator expects a uint8 image, got dtype={image.dtype}.")

    if image.ndim == 2:
        return image

    if image.ndim == 3:
        channels = image.shape[2]
        if channels == 1:
            return image[:, :, 0]
        if channels == 3:
            return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        if channels == 4:
            return cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
        raise ValueError(f"Sobel derivative operator expects 1, 3, or 4 channels, got shape={image.shape}.")

    raise ValueError(f"Sobel derivative operator expects a 2-D or 3-D array, got ndim={image.ndim}.")


class SobelDerivative(BaseOperator):
    def compute(self, image: np.ndarray) -> np.ndarray:
        """Apply the Sobel derivative operator.

        Returns a uint8 grayscale image with values in [0, 255].
        BGRA and 1-channel 3D images are converted to 2D grayscale before applying Sobel.
        """
        direction = str(self.params.get("type", "HORIZONTAL")).upper()
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

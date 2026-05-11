import cv2
import numpy as np

from app.operators.base import BaseOperator


class Laplacian(BaseOperator):
    """
    Laplacian edge detection operator.

    Applies the Laplacian second-derivative operator to detect edges.
    Complements Sobel/Canny by using a single kernel for both horizontal
    and vertical edges simultaneously.

    Params:
        ksize (int): Aperture size for the Laplacian kernel. Must be odd.
                     1 = 3x3 kernel (default), 3, 5, 7 also valid.
    """

    def __init__(self, params: dict):
        self._ksize = int(params.get("ksize", 1))

    def compute(self, image: np.ndarray) -> np.ndarray:
        if image.ndim == 3 and image.shape[2] == 4:
            image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image.copy()

        lap = cv2.Laplacian(gray, cv2.CV_64F, ksize=self._ksize)
        result = np.uint8(np.absolute(lap))
        return result

import cv2
import numpy as np

from app.operators.base import BaseOperator

_VALID_KSIZE: frozenset[int] = frozenset({1, 3, 5, 7})
_VALID_DDEPTH: frozenset[int] = frozenset({-1, cv2.CV_8U, cv2.CV_16U, cv2.CV_16S, cv2.CV_32F, cv2.CV_64F})


class Laplacian(BaseOperator):
    def compute(self, image: np.ndarray) -> np.ndarray:
        ddepth = int(self.params.get("ddepth", -1))
        if ddepth not in _VALID_DDEPTH:
            raise ValueError(f"Invalid ddepth={ddepth}; must be one of {sorted(_VALID_DDEPTH)}")

        if ddepth == -1 and np.issubdtype(image.dtype, np.integer):
            ddepth = cv2.CV_64F

        ksize = int(self.params.get("ksize", 1))
        if ksize not in _VALID_KSIZE:
            raise ValueError(f"Invalid ksize={ksize}; must be one of {sorted(_VALID_KSIZE)}")

        laplacian = cv2.Laplacian(image, ddepth, ksize=ksize)
        return np.uint8(np.absolute(laplacian))

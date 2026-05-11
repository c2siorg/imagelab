import cv2
import numpy as np

from app.operators.base import BaseOperator


class GrayImage(BaseOperator):
    def compute(self, image: np.ndarray) -> np.ndarray:
        """
        Convert *image* to a 2-D (H × W) grayscale array.

        Supported input formats
        -----------------------
        * 2-D ``(H, W)``         — already grayscale; returned as a copy.
        * 3-D ``(H, W, 1)``      — single-channel packed; channel axis is squeezed, returned as a copy.
        * 3-D ``(H, W, 3)``      — **BGR** (OpenCV convention) → grayscale.
        * 3-D ``(H, W, 4)``      — **BGRA** (OpenCV convention) → grayscale; alpha ignored.

        Raises
        ------
        ValueError
            For any other dimensionality or channel count.
        """
        if image.ndim == 2:
            return image.copy()
        elif image.ndim == 3:
            channels = image.shape[2]
            if channels == 1:
                return image[:, :, 0].copy()
            elif channels == 3:
                return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            elif channels == 4:
                return cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)

        raise ValueError(
            f"GrayImage expects a 2D or 3D image with 1/3/4 channels, got ndim={image.ndim}, shape={image.shape}"
        )

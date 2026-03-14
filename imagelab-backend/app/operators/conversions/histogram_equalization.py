import cv2
import numpy as np

from app.operators.base import BaseOperator


class HistogramEqualization(BaseOperator):
    """
    Applies global histogram equalization to improve image contrast.

    * **Grayscale** images are equalized directly via ``cv2.equalizeHist``.
    * **Colour** (BGR) images are converted to the LAB colour space so that
      only the L (lightness) channel is equalized, preserving hue and
      saturation.
    * **BGRA** images are handled like BGR with the alpha channel preserved.
    """

    def compute(self, image: np.ndarray) -> np.ndarray:
        if image.ndim == 2:
            # Grayscale — equalize directly
            return cv2.equalizeHist(image)

        if image.ndim == 3 and image.shape[2] == 4:
            # BGRA — equalize luminance, preserve alpha
            bgr = image[:, :, :3]
            alpha = image[:, :, 3]
            equalized_bgr = self._equalize_bgr(bgr)
            return np.dstack([equalized_bgr, alpha])

        # BGR (3-channel)
        return self._equalize_bgr(image)

    @staticmethod
    def _equalize_bgr(bgr: np.ndarray) -> np.ndarray:
        """Equalize the L-channel of a BGR image via LAB colour space."""
        lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)
        lightness, a, b = cv2.split(lab)
        lightness_eq = cv2.equalizeHist(lightness)
        return cv2.cvtColor(cv2.merge((lightness_eq, a, b)), cv2.COLOR_LAB2BGR)

import cv2
import numpy as np

from app.operators.base import BaseOperator


class BrightnessContrast(BaseOperator):
    """
    Applies a linear brightness and contrast transformation.

    The transformation is:  ``output = contrast * image + brightness``

    Values are saturated (clipped) to the [0, 255] range automatically
    by ``cv2.convertScaleAbs``.

    Parameters
    ----------
    brightness : int | float
        Additive brightness offset.  Range: **-100 … 100**.  Default **0**.
    contrast : float
        Multiplicative contrast factor.  Range: **0.0 … 3.0**.  Default **1.0**
        (no change).  Values < 1 reduce contrast; values > 1 increase it.
    """

    def compute(self, image: np.ndarray) -> np.ndarray:
        brightness = float(self.params.get("brightness", 0))
        contrast = float(self.params.get("contrast", 1.0))

        # Clamp to safe ranges
        brightness = max(-100.0, min(100.0, brightness))
        contrast = max(0.0, min(3.0, contrast))

        return cv2.convertScaleAbs(image, alpha=contrast, beta=brightness)

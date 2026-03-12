import cv2
import numpy as np

from app.operators.base import BaseOperator


class BrightnessContrast(BaseOperator):
    """Brightness and contrast adjustment operator.

    Parameters:
        brightness (float): Additive brightness offset. Range: [-255, 255]. Default: 0.
        contrast (float): Multiplicative contrast scale. Range: [0.0, 3.0]. Default: 1.0.
            A value of 0 produces a black image. Negative values are not allowed.
    """

    def compute(self, image: np.ndarray) -> np.ndarray:
        try:
            brightness = float(self.params.get("brightness", 0))  # range: [-255, 255]
            contrast = float(self.params.get("contrast", 1.0))  # range: [0.0, 3.0]
        except (ValueError, TypeError) as e:
            raise ValueError(f"brightness and contrast must be numeric values: {e}") from e

        if contrast < 0:
            raise ValueError(f"contrast must be non-negative, got {contrast}")

        # cv2.convertScaleAbs applies: output = |contrast * input + brightness|
        # and clips automatically to [0, 255] as uint8
        return cv2.convertScaleAbs(image, alpha=contrast, beta=brightness)

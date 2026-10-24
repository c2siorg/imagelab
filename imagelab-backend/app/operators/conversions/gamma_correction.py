import cv2
import numpy as np

from app.operators.base import BaseOperator

MIN_GAMMA = 0.1
MAX_GAMMA = 5.0


class GammaCorrection(BaseOperator):
    """Adjusts the midtones of an image with a gamma curve.

    Each pixel value v becomes 255 * (v / 255) ** (1 / gamma). Values of gamma
    above 1 brighten the midtones, values below 1 darken them, and 1.0 leaves
    the image unchanged. Black (0) and white (255) always stay the same.
    """

    def compute(self, image: np.ndarray) -> np.ndarray:
        gamma = float(self.params.get("gamma", 1.0))
        if not MIN_GAMMA <= gamma <= MAX_GAMMA:
            raise ValueError(f"'gamma' must be between {MIN_GAMMA} and {MAX_GAMMA}, got {gamma}.")
        if image.dtype != np.uint8:
            raise ValueError(f"GammaCorrection expects a uint8 image, got dtype={image.dtype}.")

        table = np.array([255 * (i / 255) ** (1 / gamma) for i in range(256)])
        table = np.clip(np.round(table), 0, 255).astype(np.uint8)

        if image.ndim == 3 and image.shape[2] == 4:
            bgr = cv2.LUT(image[:, :, :3], table)
            return np.concatenate([bgr, image[:, :, 3:4]], axis=2)
        return cv2.LUT(image, table)

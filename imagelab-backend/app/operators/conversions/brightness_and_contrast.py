import numpy as np

from app.operators.base import BaseOperator


class BrightnessAndContrast(BaseOperator):
    """
    Adjusts the brightness and contrast of an image.

    Params:
        brightnessValue (int): Additive brightness offset [-100, 100]. Clamped if out of range.
        contrastValue (float): Multiplicative contrast scale [0.0, 3.0]. 1.0 = no change.
    """

    def compute(self, image: np.ndarray) -> np.ndarray:
        """
        Apply brightness and contrast adjustment.

        Args:
            image: Input uint8 NumPy ndarray (grayscale or multi-channel).

        Returns:
            Adjusted image as a uint8 NumPy ndarray of the same shape.
        """
        if image is None or not isinstance(image, np.ndarray) or image.size == 0:
            raise ValueError("BrightnessAndContrast.compute: received an invalid or empty image")
        try:
            brightness = int(self.params.get("brightnessValue", 0))
        except (TypeError, ValueError):
            brightness = 0
        try:
            contrast = float(self.params.get("contrastValue", 1.0))
        except (TypeError, ValueError):
            contrast = 1.0

        # Ensure brightness and contrast values are within valid ranges
        # Clamp to match frontend field_number constraints in conversions.blocks.ts
        brightness = max(-100, min(100, brightness))
        contrast = max(0.0, min(3.0, contrast))

        adjusted = contrast * (image.astype(np.float32) - 128.0) + 128.0 + brightness
        return np.clip(adjusted, 0, 255).astype(np.uint8)

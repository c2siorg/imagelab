import cv2
import numpy as np

from app.operators.base import BaseOperator


class BrightnessContrast(BaseOperator):
    """
    Adjusts the brightness and contrast of an image.

    Brightness: integer shift added to each pixel.
    Contrast: multiplicative factor applied to each pixel.
    """

    def compute(self, image: np.ndarray) -> np.ndarray:
        """
        Apply Brightness and Contrast adjustment.

        Args:
            image: A uint8 NumPy array of shape (H, W), (H, W, 3) or (H, W, 4).

        Returns:
            The adjusted uint8 image.

        Raises:
            ValueError: If parameters are out of range or image type is invalid.
        """
        if image is None:
            raise ValueError("Input image cannot be None")
        if image.dtype != np.uint8:
            raise ValueError("Brightness and Contrast adjustment requires a uint8 image.")

        brightness = int(self.params.get("brightness", 0))
        contrast = float(self.params.get("contrast", 1.0))

        if not (-100 <= brightness <= 100):
            raise ValueError(f"Brightness must be between -100 and 100, got {brightness}")
        if not (0.0 <= contrast <= 3.0):
            raise ValueError(f"Contrast must be between 0.0 and 3.0, got {contrast}")

        if len(image.shape) == 3 and image.shape[2] == 4:
            # BGRA — apply to BGR, preserve alpha
            bgr = image[:, :, :3]
            alpha = image[:, :, 3]
            result_bgr = cv2.convertScaleAbs(bgr, alpha=contrast, beta=brightness)
            return np.dstack([result_bgr, alpha])
        else:
            # Grayscale or BGR
            return cv2.convertScaleAbs(image, alpha=contrast, beta=brightness)

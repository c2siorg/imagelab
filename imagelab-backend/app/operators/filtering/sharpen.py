import cv2
import numpy as np

from app.operators.base import BaseOperator


class Sharpen(BaseOperator):
    def compute(self, image: np.ndarray) -> np.ndarray:
        if image is None or not isinstance(image, np.ndarray) or image.size == 0:
            raise ValueError("Sharpen.compute: received an invalid or empty image")

        try:
            strength = float(self.params.get("strength", 1.0))
        except (TypeError, ValueError):
            strength = 1.0
        # Clamp strength to [0.0, 2.0]
        strength = max(0.0, min(2.0, strength))

        # Standard sharpening kernel
        kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]], dtype=np.float32)

        if image.ndim == 3 and image.shape[2] == 4:
            bgr = image[:, :, :3]
            sharpened_bgr = cv2.filter2D(bgr, -1, kernel)
            blended_bgr = cv2.addWeighted(bgr, 1.0 - strength, sharpened_bgr, strength, 0)
            res_bgr = np.clip(blended_bgr, 0, 255).astype(np.uint8)
            return np.dstack([res_bgr, image[:, :, 3]])

        if image.ndim == 3 and image.shape[2] == 1:
            gray = image[:, :, 0]
            sharpened_gray = cv2.filter2D(gray, -1, kernel)
            blended_gray = cv2.addWeighted(gray, 1.0 - strength, sharpened_gray, strength, 0)
            res_gray = np.clip(blended_gray, 0, 255).astype(np.uint8)
            return res_gray[:, :, np.newaxis]

        sharpened = cv2.filter2D(image, -1, kernel)
        result = cv2.addWeighted(image, 1.0 - strength, sharpened, strength, 0)
        return np.clip(result, 0, 255).astype(np.uint8)

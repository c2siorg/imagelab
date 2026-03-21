import cv2
import numpy as np

from app.operators.base import BaseOperator


class claheImage(BaseOperator):
    """
    Applies CLAHE (Contrast Limited Adaptive Histogram Equalization) to an image.

    For color images, equalization is performed on the L-channel of the
    LAB color space to avoid shifting hue or saturation.
    For grayscale images, equalization is applied directly.
    """

    def compute(self, image: np.ndarray) -> np.ndarray:
        """
        Apply CLAHE to the input image.

        Args:
            image: A uint8 NumPy array of shape (H, W) or (H, W, 3).

        Returns:
            A contrast-enhanced uint8 image of the same shape and dtype.

        Raises:
            ValueError: If the image is None or not uint8.
        """
        if image is None:
            raise ValueError("Input image cannot be None")
        if image.dtype != np.uint8:
            raise ValueError(
                f"CLAHE requires a uint8 image, but got dtype={image.dtype}. "
                "Convert the image first (e.g. (img * 255).astype(np.uint8))."
            )
        clip_limit = float(self.params.get("clipLimit", 2.0))
        grid_size = (
            int(self.params.get("tileGridSizeX", 8)),
            int(self.params.get("tileGridSizeY", 8)),
        )
        cache_key = (clip_limit, grid_size)
        if not hasattr(self, "_clahe_cache") or self._clahe_cache[0] != cache_key:
            self._clahe_cache = (
                cache_key,
                cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=grid_size),
            )
        clahe = self._clahe_cache[1]

        if len(image.shape) == 3 and image.shape[2] == 3:
            # BGR: apply CLAHE to L channel in LAB space
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            lightness, a, b = cv2.split(lab)
            l_enhanced = clahe.apply(lightness)
            enhanced_lab = cv2.merge((l_enhanced, a, b))
            return cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)

        elif image.ndim == 3 and image.shape[2] == 4:
            # BGRA: apply CLAHE to BGR channels, preserve alpha
            bgr = image[:, :, :3]
            alpha = image[:, :, 3]
            lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)
            lightness, a, b = cv2.split(lab)
            l_enhanced = clahe.apply(lightness)
            enhanced_lab = cv2.merge((l_enhanced, a, b))
            result_bgr = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
            return np.dstack([result_bgr, alpha])

        else:
            # Grayscale (H,W) or (H,W,1)
            gray = image[:, :, 0] if image.ndim == 3 else image
            return clahe.apply(gray)

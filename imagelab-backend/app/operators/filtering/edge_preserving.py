import cv2
import numpy as np

from app.operators.base import BaseOperator

_MODES: dict[str, int] = {
    "RECURS_FILTER": cv2.RECURS_FILTER,
    "NORMCONV_FILTER": cv2.NORMCONV_FILTER,
}


class EdgePreservingFilter(BaseOperator):
    """Smooth image regions while preserving sharp edges using domain transform filters.

    Supports Recursive Filter (RECURS_FILTER) for fast O(1) runtime per pixel and
    Normalized Convolution (NORMCONV_FILTER) for artifact-free edge boundaries.
    """

    def compute(self, image: np.ndarray) -> np.ndarray:
        if image is None or not isinstance(image, np.ndarray) or image.size == 0:
            raise ValueError("EdgePreservingFilter.compute: received an invalid or empty image")

        if not (image.ndim == 2 or (image.ndim == 3 and image.shape[2] in (1, 3, 4))):
            raise ValueError(
                f"EdgePreservingFilter expects a 2-D or 3-D image with 1, 3, or 4 channels, got shape {image.shape}."
            )

        if image.dtype != np.uint8:
            raise ValueError(f"EdgePreservingFilter expects a uint8 image, got dtype={image.dtype}.")

        mode_str = str(self.params.get("mode", "RECURS_FILTER")).upper()
        if mode_str not in _MODES:
            mode_str = "RECURS_FILTER"
        flags = _MODES[mode_str]

        try:
            sigma_s = float(self.params.get("sigma_s", 60.0))
        except (TypeError, ValueError):
            sigma_s = 60.0
        sigma_s = max(1.0, min(200.0, sigma_s))

        try:
            sigma_r = float(self.params.get("sigma_r", 0.4))
        except (TypeError, ValueError):
            sigma_r = 0.4
        sigma_r = max(0.01, min(1.0, sigma_r))

        if image.ndim == 3 and image.shape[2] == 4:
            bgr = image[:, :, :3]
            filtered = cv2.edgePreservingFilter(bgr, flags=flags, sigma_s=sigma_s, sigma_r=sigma_r)
            return np.dstack([filtered, image[:, :, 3]])

        if image.ndim == 3 and image.shape[2] == 1:
            gray = image[:, :, 0]
            bgr = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
            filtered = cv2.edgePreservingFilter(bgr, flags=flags, sigma_s=sigma_s, sigma_r=sigma_r)
            return cv2.cvtColor(filtered, cv2.COLOR_BGR2GRAY)[:, :, np.newaxis]

        if image.ndim == 2:
            bgr = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
            filtered = cv2.edgePreservingFilter(bgr, flags=flags, sigma_s=sigma_s, sigma_r=sigma_r)
            return cv2.cvtColor(filtered, cv2.COLOR_BGR2GRAY)

        return cv2.edgePreservingFilter(image, flags=flags, sigma_s=sigma_s, sigma_r=sigma_r)

import cv2
import numpy as np

from app.operators.base import BaseOperator
from app.utils.color import hex_to_bgr


class CornerDetection(BaseOperator):
    """Detect image corners using Shi-Tomasi or Harris corner detection.

    Runs cv2.goodFeaturesToTrack on a grayscale version of the image and marks
    the detected corner coordinates with circle indicators.
    """

    def compute(self, image: np.ndarray) -> np.ndarray:
        if image is None or not isinstance(image, np.ndarray) or image.size == 0:
            raise ValueError("CornerDetection received an invalid or empty image.")

        if not (image.ndim == 2 or (image.ndim == 3 and image.shape[2] in (1, 3, 4))):
            raise ValueError(
                f"CornerDetection expects a 2-D or 3-D image with 1, 3, or 4 channels, got shape {image.shape}."
            )

        if image.dtype != np.uint8:
            raise ValueError(f"CornerDetection expects a uint8 image, got dtype={image.dtype}.")

        method = str(self.params.get("method", "SHI_TOMASI")).upper()
        if method not in ("SHI_TOMASI", "HARRIS"):
            method = "SHI_TOMASI"
        use_harris = method == "HARRIS"

        try:
            max_corners = int(self.params.get("maxCorners", 50))
        except (TypeError, ValueError):
            max_corners = 50
        max_corners = max(1, min(1000, max_corners))

        try:
            quality_level = float(self.params.get("qualityLevel", 0.01))
        except (TypeError, ValueError):
            quality_level = 0.01
        quality_level = max(0.001, min(1.0, quality_level))

        try:
            min_distance = float(self.params.get("minDistance", 10.0))
        except (TypeError, ValueError):
            min_distance = 10.0
        min_distance = max(1.0, min(500.0, min_distance))

        try:
            block_size = int(self.params.get("blockSize", 3))
        except (TypeError, ValueError):
            block_size = 3
        if block_size < 3:
            block_size = 3
        elif block_size % 2 == 0:
            block_size += 1
        block_size = min(31, block_size)

        try:
            k = float(self.params.get("k", 0.04))
        except (TypeError, ValueError):
            k = 0.04
        k = max(0.01, min(0.2, k))

        try:
            radius = int(self.params.get("radius", 4))
        except (TypeError, ValueError):
            radius = 4
        radius = max(1, min(50, radius))

        try:
            thickness = int(self.params.get("thickness", -1))
        except (TypeError, ValueError):
            thickness = -1
        if thickness != -1 and thickness < 1:
            thickness = -1

        bgr_color = hex_to_bgr(self.params.get("rgbcolors_input", "#ff0000"))

        # Convert to single-channel grayscale for corner detection
        if image.ndim == 2:
            gray = image
            result = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
            draw_color = bgr_color
        elif image.ndim == 3 and image.shape[2] == 1:
            gray = image[:, :, 0]
            result = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
            draw_color = bgr_color
        elif image.ndim == 3 and image.shape[2] == 4:
            gray = cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
            result = image.copy()
            draw_color = (*bgr_color, 255)
        else:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            result = image.copy()
            draw_color = bgr_color

        corners = cv2.goodFeaturesToTrack(
            gray,
            maxCorners=max_corners,
            qualityLevel=quality_level,
            minDistance=min_distance,
            blockSize=block_size,
            useHarrisDetector=use_harris,
            k=k,
        )

        if corners is not None:
            for pt in corners:
                x, y = map(int, pt.ravel())
                cv2.circle(result, (x, y), radius, draw_color, thickness)

        return result

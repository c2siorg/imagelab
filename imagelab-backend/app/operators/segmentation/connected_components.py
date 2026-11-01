import cv2
import numpy as np

from app.operators.base import BaseOperator
from app.utils.color import hex_to_bgr


class ConnectedComponents(BaseOperator):
    """Labels and analyzes connected components in an image using cv2.connectedComponentsWithStats.

    Extracts disjoint foreground regions, computes statistics (area, bounding box,
    centroid), filters out small noise components below min_area, and visualizes
    them using color mapping, bounding boxes, or centroid markers.
    """

    def compute(self, image: np.ndarray) -> np.ndarray:
        if image is None or not isinstance(image, np.ndarray) or image.size == 0:
            raise ValueError("ConnectedComponents received an invalid or empty image.")

        if not (image.ndim == 2 or (image.ndim == 3 and image.shape[2] in (1, 3, 4))):
            raise ValueError(
                f"ConnectedComponents expects a 2-D or 3-D image with 1, 3, or 4 channels, got shape {image.shape}."
            )

        if image.dtype != np.uint8:
            raise ValueError(f"ConnectedComponents expects a uint8 image, got dtype={image.dtype}.")

        try:
            connectivity = int(self.params.get("connectivity", 8))
        except (TypeError, ValueError):
            connectivity = 8
        if connectivity not in (4, 8):
            connectivity = 8

        output_mode = str(self.params.get("output_mode", "COLOR_MAP")).upper()
        if output_mode not in ("COLOR_MAP", "BOUNDING_BOX", "CENTROID"):
            output_mode = "COLOR_MAP"

        raw_invert = self.params.get("invert", False)
        invert = raw_invert == "TRUE" if isinstance(raw_invert, str) else bool(raw_invert)

        try:
            min_area = int(self.params.get("min_area", 50))
        except (TypeError, ValueError):
            min_area = 50
        min_area = max(0, min(100000, min_area))

        try:
            thickness = int(self.params.get("thickness", 2))
        except (TypeError, ValueError):
            thickness = 2
        thickness = max(1, min(20, thickness))

        bgr_color = hex_to_bgr(self.params.get("rgbcolors_input", "#00ffff"))

        # Convert to single-channel 8-bit mask for connected component analysis
        if image.ndim == 2:
            gray = image
        elif image.ndim == 3 and image.shape[2] == 1:
            gray = image[:, :, 0]
        elif image.ndim == 3 and image.shape[2] == 4:
            gray = cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
        else:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        binary = (gray > 0).astype(np.uint8) * 255
        if invert:
            binary = cv2.bitwise_not(binary)

        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary, connectivity=connectivity)

        if output_mode == "COLOR_MAP":
            if num_labels <= 1:
                result = np.zeros((*gray.shape[:2], 3), dtype=np.uint8)
            else:
                colors = np.zeros((num_labels, 3), dtype=np.uint8)
                for i in range(1, num_labels):
                    if stats[i, cv2.CC_STAT_AREA] >= min_area:
                        hue = (i * 37) % 180
                        colors[i] = [hue, 255, 255]
                bgr_lut = cv2.cvtColor(colors[None, :, :], cv2.COLOR_HSV2BGR)[0]
                bgr_lut[0] = [0, 0, 0]
                for i in range(1, num_labels):
                    if stats[i, cv2.CC_STAT_AREA] < min_area:
                        bgr_lut[i] = [0, 0, 0]
                result = bgr_lut[labels]

            if image.ndim == 3 and image.shape[2] == 4:
                return np.concatenate([result, image[:, :, 3:4]], axis=2)
            return result

        # Bounding box and Centroid modes draw on top of the original image
        if image.ndim == 2 or (image.ndim == 3 and image.shape[2] == 1):
            result = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
            draw_color = bgr_color
        elif image.ndim == 3 and image.shape[2] == 4:
            result = image.copy()
            draw_color = (*bgr_color, 255)
        else:
            result = image.copy()
            draw_color = bgr_color

        if output_mode == "BOUNDING_BOX":
            for i in range(1, num_labels):
                if stats[i, cv2.CC_STAT_AREA] >= min_area:
                    x = int(stats[i, cv2.CC_STAT_LEFT])
                    y = int(stats[i, cv2.CC_STAT_TOP])
                    w = int(stats[i, cv2.CC_STAT_WIDTH])
                    h = int(stats[i, cv2.CC_STAT_HEIGHT])
                    cv2.rectangle(result, (x, y), (x + w, y + h), draw_color, thickness)
        else:  # CENTROID
            radius = max(3, thickness * 2)
            for i in range(1, num_labels):
                if stats[i, cv2.CC_STAT_AREA] >= min_area:
                    cx = int(round(centroids[i, 0]))
                    cy = int(round(centroids[i, 1]))
                    cv2.circle(result, (cx, cy), radius, draw_color, -1)

        return result

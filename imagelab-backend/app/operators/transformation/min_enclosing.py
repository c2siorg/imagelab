import cv2
import numpy as np

from app.operators.base import BaseOperator
from app.utils.color import hex_to_bgr


def _safe_int(val: object, default: int) -> int:
    try:
        return int(float(str(val).strip()))
    except (TypeError, ValueError):
        return default


def _safe_float(val: object, default: float) -> float:
    try:
        return float(str(val).strip())
    except (TypeError, ValueError):
        return default


class MinEnclosing(BaseOperator):
    """Computes minimum enclosing and bounding geometries for shapes in an image.

    Extracts external contours using cv2.findContours, then calculates and draws
    ideal geometric bounding primitives:
    - ROTATED_BOX: Minimal-area oriented bounding rectangle (cv2.minAreaRect)
    - ENCLOSING_CIRCLE: Minimal enclosing circle (cv2.minEnclosingCircle)
    - FIT_ELLIPSE: Fitted bounding ellipse (cv2.fitEllipse)
    - ALL_SHAPES: Renders rotated rectangle, circle, and ellipse simultaneously

    Note:
        Operates on pre-thresholded, binary, or high-contrast shape imagery (e.g.,
        preceded by a Thresholding or Canny Edge block). Raw photographic inputs
        without zero-valued background pixels will treat the entire outer frame
        as a single bounding contour.
    """

    def compute(self, image: np.ndarray) -> np.ndarray:
        if image is None or not isinstance(image, np.ndarray) or image.size == 0:
            raise ValueError("MinEnclosing received an invalid or empty image.")

        if not (image.ndim == 2 or (image.ndim == 3 and image.shape[2] in (1, 3, 4))):
            raise ValueError(
                f"MinEnclosing expects a 2-D or 3-D image with 1, 3, or 4 channels, got shape {image.shape}."
            )

        if image.dtype != np.uint8:
            raise ValueError(f"MinEnclosing expects a uint8 image, got dtype={image.dtype}.")

        geometry = str(self.params.get("geometry", "ROTATED_BOX")).upper()
        if geometry not in ("ROTATED_BOX", "ENCLOSING_CIRCLE", "FIT_ELLIPSE", "ALL_SHAPES"):
            geometry = "ROTATED_BOX"

        min_area = max(0, min(100000, _safe_int(self.params.get("min_area", 50), 50)))
        thickness = max(1, min(20, _safe_int(self.params.get("thickness", 2), 2)))

        raw_sc = self.params.get("show_contours", False)
        show_contours = raw_sc == "TRUE" if isinstance(raw_sc, str) else bool(raw_sc)

        try:
            box_bgr = hex_to_bgr(self.params.get("box_color", "#00ffff"))
        except (TypeError, ValueError):
            box_bgr = (255, 255, 0)

        try:
            circle_bgr = hex_to_bgr(self.params.get("circle_color", "#ff00ff"))
        except (TypeError, ValueError):
            circle_bgr = (255, 0, 255)

        try:
            ellipse_bgr = hex_to_bgr(self.params.get("ellipse_color", "#ffff00"))
        except (TypeError, ValueError):
            ellipse_bgr = (0, 255, 255)

        # Convert to single-channel 8-bit image for contour extraction
        # Maintain original channel count (no unexpected mutation for downstream operators)
        if image.ndim == 2:
            gray = image
            result = image.copy()
            box_draw = int(np.mean(box_bgr))
            circle_draw = int(np.mean(circle_bgr))
            ellipse_draw = int(np.mean(ellipse_bgr))
            contour_draw = 128
        elif image.ndim == 3 and image.shape[2] == 1:
            gray = image[:, :, 0]
            result = image.copy()
            box_draw = int(np.mean(box_bgr))
            circle_draw = int(np.mean(circle_bgr))
            ellipse_draw = int(np.mean(ellipse_bgr))
            contour_draw = 128
        elif image.ndim == 3 and image.shape[2] == 4:
            gray = cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
            result = image.copy()
            box_draw = (*box_bgr, 255)
            circle_draw = (*circle_bgr, 255)
            ellipse_draw = (*ellipse_bgr, 255)
            contour_draw = (128, 128, 128, 255)
        else:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            result = image.copy()
            box_draw = box_bgr
            circle_draw = circle_bgr
            ellipse_draw = ellipse_bgr
            contour_draw = (128, 128, 128)

        contours, _ = cv2.findContours(gray, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < min_area or len(cnt) < 3:
                continue

            if show_contours:
                cv2.drawContours(result, [cnt], -1, contour_draw, 1)

            # 1. Rotated Bounding Rectangle (cv2.minAreaRect)
            if geometry in ("ROTATED_BOX", "ALL_SHAPES"):
                try:
                    rect = cv2.minAreaRect(cnt)
                    box = cv2.boxPoints(rect)
                    box_pts = np.int32(np.round(box))
                    cv2.drawContours(result, [box_pts], 0, box_draw, thickness)
                except cv2.error:
                    pass

            # 2. Minimal Enclosing Circle (cv2.minEnclosingCircle)
            if geometry in ("ENCLOSING_CIRCLE", "ALL_SHAPES"):
                try:
                    (cx, cy), radius = cv2.minEnclosingCircle(cnt)
                    center = (int(round(cx)), int(round(cy)))
                    rad = int(round(radius))
                    cv2.circle(result, center, rad, circle_draw, thickness)
                except cv2.error:
                    pass

            # 3. Fitted Ellipse (cv2.fitEllipse requires at least 5 contour points)
            if geometry in ("FIT_ELLIPSE", "ALL_SHAPES") and len(cnt) >= 5:
                try:
                    ellipse = cv2.fitEllipse(cnt)
                    cv2.ellipse(result, ellipse, ellipse_draw, thickness)
                except cv2.error:
                    pass

        return result

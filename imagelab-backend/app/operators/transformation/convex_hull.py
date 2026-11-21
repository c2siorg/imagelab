import contextlib

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


class ConvexHull(BaseOperator):
    """Computes the convex hull and convexity defects of shapes in an image.

    Extracts contours using cv2.findContours, calculates the minimal enclosing
    convex polygon using cv2.convexHull, and optionally marks convexity defects
    (indentation points) using cv2.convexityDefects.

    Note:
        Operates on pre-thresholded, binary, or high-contrast shape imagery (e.g.,
        preceded by a Thresholding or Canny Edge block). Raw photographic inputs
        without zero-valued background pixels will treat the entire outer frame
        as a single bounding contour.
    """

    def compute(self, image: np.ndarray) -> np.ndarray:
        if image is None or not isinstance(image, np.ndarray) or image.size == 0:
            raise ValueError("ConvexHull received an invalid or empty image.")

        if not (image.ndim == 2 or (image.ndim == 3 and image.shape[2] in (1, 3, 4))):
            raise ValueError(
                f"ConvexHull expects a 2-D or 3-D image with 1, 3, or 4 channels, got shape {image.shape}."
            )

        if image.dtype != np.uint8:
            raise ValueError(f"ConvexHull expects a uint8 image, got dtype={image.dtype}.")

        mode = str(self.params.get("mode", "HULL_AND_DEFECTS")).upper()
        if mode not in ("HULL_ONLY", "HULL_AND_DEFECTS"):
            mode = "HULL_AND_DEFECTS"

        min_area = max(0, min(100000, _safe_int(self.params.get("min_area", 50), 50)))
        min_defect_depth = max(0.0, min(500.0, _safe_float(self.params.get("min_defect_depth", 5.0), 5.0)))
        thickness = max(1, min(20, _safe_int(self.params.get("thickness", 2), 2)))

        raw_sc = self.params.get("show_contours", False)
        show_contours = raw_sc == "TRUE" if isinstance(raw_sc, str) else bool(raw_sc)

        try:
            hull_bgr = hex_to_bgr(self.params.get("hull_color", "#00ffff"))
        except (TypeError, ValueError):
            hull_bgr = (255, 255, 0)

        try:
            defect_bgr = hex_to_bgr(self.params.get("defect_color", "#ff0000"))
        except (TypeError, ValueError):
            defect_bgr = (0, 0, 255)

        # Convert to single-channel 8-bit image for contour extraction
        # Maintain original channel count (no unexpected mutation for downstream operators)
        if image.ndim == 2:
            gray = image
            result = image.copy()
            hull_draw = int(np.mean(hull_bgr))
            defect_draw = int(np.mean(defect_bgr))
            contour_draw = 200
        elif image.ndim == 3 and image.shape[2] == 1:
            gray = image[:, :, 0]
            result = image.copy()
            hull_draw = int(np.mean(hull_bgr))
            defect_draw = int(np.mean(defect_bgr))
            contour_draw = 200
        elif image.ndim == 3 and image.shape[2] == 4:
            gray = cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
            result = image.copy()
            hull_draw = (*hull_bgr, 255)
            defect_draw = (*defect_bgr, 255)
            contour_draw = (200, 200, 200, 255)
        else:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            result = image.copy()
            hull_draw = hull_bgr
            defect_draw = defect_bgr
            contour_draw = (200, 200, 200)

        contours, _ = cv2.findContours(gray, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        defect_radius = max(3, thickness * 2)

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < min_area or len(cnt) < 3:
                continue

            if show_contours:
                with contextlib.suppress(cv2.error):
                    cv2.drawContours(result, [cnt], -1, contour_draw, 1)

            try:
                hull_pts = cv2.convexHull(cnt, returnPoints=True)
                if hull_pts is not None and len(hull_pts) > 0:
                    cv2.drawContours(result, [hull_pts], -1, hull_draw, thickness)
            except cv2.error:
                continue

            if mode == "HULL_AND_DEFECTS" and len(cnt) >= 4:
                with contextlib.suppress(cv2.error):
                    hull_indices = cv2.convexHull(cnt, returnPoints=False)
                    if hull_indices is not None and len(hull_indices) >= 3:
                        hull_indices = np.sort(hull_indices, axis=0)
                        defects = cv2.convexityDefects(cnt, hull_indices)
                        if defects is not None:
                            for d in defects:
                                _start, _end, far_idx, fix_depth = d[0]
                                depth = fix_depth / 256.0
                                if depth >= min_defect_depth:
                                    far_pt = tuple(map(int, cnt[far_idx][0]))
                                    cv2.circle(result, far_pt, defect_radius, defect_draw, -1)

        return result

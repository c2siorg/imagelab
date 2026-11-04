import cv2
import numpy as np

from app.operators.base import BaseOperator


def _safe_int(val: object, default: int, min_val: int | None = None, max_val: int | None = None) -> int:
    try:
        res = int(val)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        res = default
    if min_val is not None:
        res = max(min_val, res)
    if max_val is not None:
        res = min(max_val, res)
    return res


def _has_collinear_triplet(points: np.ndarray, tol: float = 1e-4) -> bool:
    """Return True if any 3 points among the 4 are collinear (degenerate quad)."""
    triplets = ((0, 1, 2), (0, 1, 3), (0, 2, 3), (1, 2, 3))
    for i, j, k in triplets:
        x1, y1 = points[i]
        x2, y2 = points[j]
        x3, y3 = points[k]
        twice_area = (x2 - x1) * (y3 - y1) - (x3 - x1) * (y2 - y1)
        if abs(float(twice_area)) < tol:
            return True
    return False


class PerspectiveTransform(BaseOperator):
    """Apply a 4-point perspective transformation (homography) to an image.

    Maps 4 source quadrilateral points to 4 destination quadrilateral points
    using cv2.getPerspectiveTransform and cv2.warpPerspective. Commonly used for
    document scanning, rectification, keystone correction, and bird's-eye projection.
    """

    def compute(self, image: np.ndarray) -> np.ndarray:
        if image is None or not isinstance(image, np.ndarray) or image.size == 0:
            raise ValueError("PerspectiveTransform received an invalid or empty image.")

        if image.ndim not in (2, 3):
            raise ValueError(f"PerspectiveTransform expects a 2-D or 3-D image, got shape {image.shape}.")

        rows, cols = image.shape[:2]
        if rows < 2 or cols < 2:
            return image

        # Default corners span the image quadrilateral: TL, TR, BR, BL
        default_corners = [
            (0.0, 0.0),
            (float(cols - 1), 0.0),
            (float(cols - 1), float(rows - 1)),
            (0.0, float(rows - 1)),
        ]

        src = np.float32([self._point("src", i, dx, dy) for i, (dx, dy) in enumerate(default_corners, 1)])
        dst = np.float32([self._point("dst", i, dx, dy) for i, (dx, dy) in enumerate(default_corners, 1)])

        # Guard against collinear or degenerate points which produce singular homographies
        if _has_collinear_triplet(src) or _has_collinear_triplet(dst):
            return image

        out_w = _safe_int(self.params.get("output_width", cols), default=cols, min_val=1, max_val=10000)
        out_h = _safe_int(self.params.get("output_height", rows), default=rows, min_val=1, max_val=10000)

        try:
            m = cv2.getPerspectiveTransform(src, dst)
            if m is None or np.allclose(m[:2, :2], 0):
                return image
            warped = cv2.warpPerspective(
                image,
                m,
                (out_w, out_h),
                flags=cv2.INTER_LINEAR,
                borderMode=cv2.BORDER_CONSTANT,
            )
            if image.ndim == 3 and image.shape[2] == 1 and warped.ndim == 2:
                warped = warped[:, :, np.newaxis]
            return warped
        except cv2.error:
            return image

    def _point(self, prefix: str, index: int, default_x: float, default_y: float) -> list[float]:
        try:
            x = float(self.params.get(f"{prefix}_x{index}", default_x))
        except (TypeError, ValueError):
            x = default_x
        try:
            y = float(self.params.get(f"{prefix}_y{index}", default_y))
        except (TypeError, ValueError):
            y = default_y
        return [x, y]

import cv2
import numpy as np

from app.operators.base import BaseOperator


class AffineImage(BaseOperator):
    def compute(self, image: np.ndarray) -> np.ndarray:
        rows, cols = image.shape[:2]

        # Pipelines saved by the old two-field block only carry translate_x /
        # translate_y. Honour them by shifting the default destination triangle,
        # which reproduces the old translation-only behaviour.
        tx = float(self.params.get("translate_x", 0))
        ty = float(self.params.get("translate_y", 0))

        # Default triangle spans the image corners so unconfigured params scale
        # with the input; with src == dst it is the identity mapping.
        corners = [(0, 0), (cols - 1, 0), (0, rows - 1)]
        src = np.float32([self._point("src", i, x, y) for i, (x, y) in enumerate(corners, 1)])
        dst = np.float32([self._point("dst", i, x + tx, y + ty) for i, (x, y) in enumerate(corners, 1)])

        # Collinear source points have no affine solution. cv2 returns an
        # all-zero matrix instead of raising, which would collapse the image
        # into a single pixel, so leave the image untouched instead.
        if _is_collinear(src):
            return image

        M = cv2.getAffineTransform(src, dst)
        return cv2.warpAffine(image, M, (cols, rows))

    def _point(self, prefix: str, index: int, default_x: float, default_y: float) -> list[float]:
        x = float(self.params.get(f"{prefix}_x{index}", default_x))
        y = float(self.params.get(f"{prefix}_y{index}", default_y))
        return [x, y]


def _is_collinear(points: np.ndarray) -> bool:
    (x1, y1), (x2, y2), (x3, y3) = points
    twice_area = (x2 - x1) * (y3 - y1) - (x3 - x1) * (y2 - y1)
    return abs(float(twice_area)) < 1e-6

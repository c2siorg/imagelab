import math

import cv2
import numpy as np

from app.operators.base import BaseOperator


class AffineImage(BaseOperator):
    DEFAULT_TX = 50.0
    DEFAULT_TY = 100.0

    def compute(self, image: np.ndarray) -> np.ndarray:
        rows, cols = image.shape[:2]

        try:
            tx = float(self.params.get("tx", self.DEFAULT_TX))
            ty = float(self.params.get("ty", self.DEFAULT_TY))
        except (TypeError, ValueError):
            tx, ty = self.DEFAULT_TX, self.DEFAULT_TY

        if not math.isfinite(tx) or not math.isfinite(ty):
            tx, ty = self.DEFAULT_TX, self.DEFAULT_TY

        tx = max(-cols, min(cols, tx))
        ty = max(-rows, min(rows, ty))

        M = np.float64([[1, 0, tx], [0, 1, ty]])
        return cv2.warpAffine(image, M, (cols, rows))

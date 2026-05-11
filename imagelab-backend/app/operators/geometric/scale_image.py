import math

import cv2
import numpy as np

from app.operators.base import BaseOperator

_INTERPOLATION_MAP: dict[str, int] = {
    "LINEAR": cv2.INTER_LINEAR,
    "AREA": cv2.INTER_AREA,
    "CUBIC": cv2.INTER_CUBIC,
    "NEAREST": cv2.INTER_NEAREST,
    "LANCZOS4": cv2.INTER_LANCZOS4,
}


class ScaleImage(BaseOperator):
    def compute(self, image: np.ndarray) -> np.ndarray:
        try:
            fx = float(self.params.get("fx", 1))
            fy = float(self.params.get("fy", 1))
        except (TypeError, ValueError) as e:
            raise ValueError(f"fx and fy must be numeric values: {e}") from e

        if not math.isfinite(fx) or not math.isfinite(fy):
            raise ValueError(f"fx and fy must be finite numeric values, got fx={fx}, fy={fy}")

        if fx <= 0:
            raise ValueError(f"fx must be greater than 0, got {fx}")
        if fy <= 0:
            raise ValueError(f"fy must be greater than 0, got {fy}")

        interpolation_str = str(self.params.get("interpolation", "LINEAR")).upper()
        if interpolation_str not in _INTERPOLATION_MAP:
            raise ValueError(
                f"Unknown interpolation '{interpolation_str}'. Valid options: {list(_INTERPOLATION_MAP.keys())}"
            )
        interpolation_flag = _INTERPOLATION_MAP[interpolation_str]

        rows, cols = image.shape[:2]
        new_size = (max(1, int(cols * fx)), max(1, int(rows * fy)))
        return cv2.resize(image, new_size, interpolation=interpolation_flag)

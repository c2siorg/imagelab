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
        fx = float(self.params.get("fx", 1))
        fy = float(self.params.get("fy", 1))

        interpolation_str = str(self.params.get("interpolation", "LINEAR")).upper()
        if interpolation_str not in _INTERPOLATION_MAP:
            raise ValueError(
                f"Unknown interpolation '{interpolation_str}'. Valid options: {list(_INTERPOLATION_MAP.keys())}"
            )
        interpolation_flag = _INTERPOLATION_MAP[interpolation_str]

        return cv2.resize(image, dsize=(0, 0), fx=fx, fy=fy, interpolation=interpolation_flag)

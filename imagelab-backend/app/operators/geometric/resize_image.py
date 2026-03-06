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


class ResizeImage(BaseOperator):
    def compute(self, image: np.ndarray) -> np.ndarray:
        # Default fallback to original dimensions if invalid or not set
        original_rows, original_cols = image.shape[:2]

        try:
            width = int(round(float(self.params.get("width", original_cols))))
            height = int(round(float(self.params.get("height", original_rows))))
        except (ValueError, TypeError):
            width = original_cols
            height = original_rows

        # Validate dimensions individually. Defaults to current length on that axis.
        if width < 1:
            width = original_cols
        if height < 1:
            height = original_rows

        # Resolve interpolation before the no-op check so invalid strings are never silently ignored
        interpolation_method_str = str(self.params.get("interpolation", "LINEAR")).upper()
        # Default to INTER_LINEAR if the method isn't explicitly found
        interpolation_flag = _INTERPOLATION_MAP.get(interpolation_method_str, cv2.INTER_LINEAR)

        # Pure No-op shortcut — return a copy for consistent ownership semantics
        if width == original_cols and height == original_rows:
            return image.copy()

        return cv2.resize(image, (width, height), interpolation=interpolation_flag)

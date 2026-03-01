import cv2
import numpy as np

from app.operators.base import BaseOperator


class ResizeImage(BaseOperator):
    def compute(self, image: np.ndarray) -> np.ndarray:
        # Default fallback to original dimensions if invalid or not set
        original_rows, original_cols = image.shape[:2]

        try:
            width = int(self.params.get("width", original_cols))
            height = int(self.params.get("height", original_rows))
        except (ValueError, TypeError):
            width = original_cols
            height = original_rows

        # Validate dimensions individually. Defaults to current length on that axis.
        if width < 1:
            width = original_cols
        if height < 1:
            height = original_rows

        # Pure No-op shortcut
        if width == original_cols and height == original_rows:
            return image

        interpolation_method_str = str(self.params.get("interpolation", "LINEAR")).upper()

        interpolation_map = {
            "LINEAR": cv2.INTER_LINEAR,
            "AREA": cv2.INTER_AREA,
            "CUBIC": cv2.INTER_CUBIC,
            "NEAREST": cv2.INTER_NEAREST,
            "LANCZOS4": cv2.INTER_LANCZOS4,
        }

        # Default to INTER_LINEAR if the method isn't explicitly found
        interpolation_flag = interpolation_map.get(interpolation_method_str, cv2.INTER_LINEAR)

        return cv2.resize(image, (width, height), interpolation=interpolation_flag)

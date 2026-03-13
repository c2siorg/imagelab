import cv2
import numpy as np

from app.operators.base import BaseOperator
from app.utils.color import hex_to_bgr

_BORDER_TYPES = {
    "CONSTANT": cv2.BORDER_CONSTANT,
    "REFLECT": cv2.BORDER_REFLECT,
    "REPLICATE": cv2.BORDER_REPLICATE,
}


class ApplyBorders(BaseOperator):
    """
    Adds a border around an image.
    
    Supports constant, reflect, and replicate border types.
    
    Parameters:
      - ``border_all_sides``: Set same width for all sides.
      - ``borderTop``, ``borderBottom``, ``borderLeft``, ``borderRight``: Side-specific widths.
      - ``borderType``: One of "CONSTANT", "REFLECT", "REPLICATE".
      - ``borderColor``: Hex string for constant border (default "#000000").
    """
    def compute(self, image: np.ndarray) -> np.ndarray:
        border_all = self.params.get("border_all_sides")
        if border_all is not None:
            top = bottom = left = right = int(border_all)
        else:
            top = int(self.params.get("borderTop", 0))
            bottom = int(self.params.get("borderBottom", 0))
            left = int(self.params.get("borderLeft", 0))
            right = int(self.params.get("borderRight", 0))

        if any(v < 0 for v in (top, bottom, left, right)):
            raise ValueError(
                f"Border widths must be non-negative. Got: top={top}, bottom={bottom}, left={left}, right={right}"
            )

        border_type_str = str(self.params.get("borderType", "CONSTANT")).upper()
        border_type = _BORDER_TYPES.get(border_type_str, cv2.BORDER_CONSTANT)
        
        hex_color = self.params.get("borderColor", "#000000")
        bgr_value = hex_to_bgr(hex_color)

        if len(image.shape) == 3 and image.shape[2] == 4:
            # For BGRA, append 255 (fully opaque) to the BGR color scalar
            border_color_full = (*bgr_value, 255)
            # OpenCV handles 4-element tuple for 4-channel images
            return cv2.copyMakeBorder(image, top, bottom, left, right, border_type, value=border_color_full)
        
        return cv2.copyMakeBorder(image, top, bottom, left, right, border_type, value=bgr_value)


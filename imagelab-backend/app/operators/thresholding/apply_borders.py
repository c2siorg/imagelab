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
            raise ValueError(f"Border widths must be non-negative. Got: top={top}, bottom={bottom}, left={left}, right={right}")

        border_type_str = str(self.params.get("borderType", "CONSTANT")).upper()
        border_type = _BORDER_TYPES.get(border_type_str, cv2.BORDER_CONSTANT)
        
        hex_color = self.params.get("borderColor", "#000000")
        bgr_value = hex_to_bgr(hex_color)

        return cv2.copyMakeBorder(image, top, bottom, left, right, border_type, value=bgr_value)


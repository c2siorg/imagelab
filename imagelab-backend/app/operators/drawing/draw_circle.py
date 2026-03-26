import cv2
import numpy as np

from app.operators.base import BaseOperator
from app.operators.drawing.validators import DrawingValidator
from app.utils.color import hex_to_bgr


class DrawCircle(BaseOperator):
    def compute(self, image: np.ndarray) -> np.ndarray:
        result = image.copy()
        thickness = DrawingValidator.validate_thickness(self.params.get("thickness", 2))
        radius = DrawingValidator.validate_axis(self.params.get("radius", 5))
        color = hex_to_bgr(self.params.get("rgbcolors_input", "#2828cc"))
        cx = int(self.params.get("center_point_x", 0))
        cy = int(self.params.get("center_point_y", 0))
        cv2.circle(result, (cx, cy), radius, color, thickness)
        return result

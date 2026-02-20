import cv2
import numpy as np

from app.operators.base import BaseOperator
from app.utils.color import hex_to_bgr


class DrawEllipse(BaseOperator):
    def compute(self, image: np.ndarray) -> np.ndarray:
        result = image.copy()
        thickness = int(self.params.get("thickness", 2))
        height = int(self.params.get("height", 0))
        width = int(self.params.get("width", 0))
        angle = int(self.params.get("angle", 90))
        color = hex_to_bgr(self.params.get("rgbcolors_input", "#2828cc"))
        cx = int(self.params.get("center_point_x", 0))
        cy = int(self.params.get("center_point_y", 0))
        cv2.ellipse(result, (cx, cy), (height, width), angle, 0, 360, color, thickness)
        return result
